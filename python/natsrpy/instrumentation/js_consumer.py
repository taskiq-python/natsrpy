from collections.abc import AsyncGenerator, Callable
from types import TracebackType
from typing import Any

from opentelemetry import context, propagate, trace  # type: ignore
from opentelemetry.instrumentation.utils import is_instrumentation_enabled, unwrap
from opentelemetry.trace import Link, SpanKind, Tracer, get_current_span
from typing_extensions import Self
from wrapt import ObjectProxy, wrap_function_wrapper

from natsrpy.instrumentation.ctx_manager_wrapper import AsyncCtxManagerProxy
from natsrpy.instrumentation.span_builder import SpanAction, SpanBuilder
from natsrpy.js import (
    JetStreamMessage,
    MessagesIterator,
    PullConsumer,
    PullConsumerFetcher,
    PushConsumer,
)


class MessagesIteratorProxy(ObjectProxy):  # type: ignore
    """Proxy for iterable subscriptions."""

    def __init__(
        self,
        wrapped: MessagesIterator,
        tracer: Tracer,
        capture_body: bool,
        capture_headers: bool,
    ) -> None:
        super().__init__(wrapped)
        # Proxy-local attrs should have _self_ prefix
        self._self_tracer = tracer
        self._self_cancel_ctx: tuple[Any, Any] | None = None
        self._self_capture_body = capture_body
        self._self_capture_headers = capture_headers

    def __aiter__(self) -> Self:
        return self

    def __cancel_ctx__(
        self,
        typ: type[BaseException] | None = None,
        exc: BaseException | None = None,
        tb: TracebackType | None = None,
    ) -> None:
        if self._self_cancel_ctx is None:
            return
        token, span_ctx = self._self_cancel_ctx
        span_ctx.__exit__(typ, exc, tb)
        context.detach(token)
        self._self_cancel_ctx = None

    async def __anext__(self) -> Any:
        # We cancel previous context if any.
        self.__cancel_ctx__()
        # Getting next message
        next_msg: JetStreamMessage = await anext(self.__wrapped__)
        if not is_instrumentation_enabled():
            return next_msg
        new_ctx = propagate.extract(next_msg.headers)
        token = context.attach(new_ctx)
        span = (
            SpanBuilder(self._self_tracer, SpanKind.CONSUMER, SpanAction.RECEIVE)
            .with_js_message(
                next_msg,
                capture_body=self._self_capture_body,
                capture_headers=self._self_capture_headers,
            )
            .build()
        )
        span_ctx = trace.use_span(span, end_on_exit=True)
        span_ctx.__enter__()
        self._self_cancel_ctx = (token, span_ctx)

        return next_msg


class JSConsumerInstrumentation:
    """
    Implementation of OpenTelemetry instrumentation for JetStream consumers.

    This instrumentation covers Push and Pull based consumers.
    """

    def __init__(
        self,
        tracer: Tracer,
        capture_headers: bool = False,
        capture_body: bool = False,
    ) -> None:
        self.tracer = tracer
        self.capture_headers = capture_headers
        self.capture_body = capture_body

    def instrument(self) -> None:
        """Setup instrumentation for both consumers."""
        self.instrument_pull()
        self.instrument_push()
        self.instrument_message()

    @classmethod
    def uninstrument(cls) -> None:
        """Unwrap Jetstream message methods."""
        # Push-consumer
        unwrap(PushConsumer, "consume")
        # Pull-consumer
        unwrap(PullConsumer, "consume")
        unwrap(PullConsumer, "fetch")
        # Message
        unwrap(JetStreamMessage, "ack")
        unwrap(JetStreamMessage, "nack")
        unwrap(JetStreamMessage, "progress")
        unwrap(JetStreamMessage, "term")
        unwrap(JetStreamMessage, "next")

    def instrument_push(self) -> None:
        """
        Instrument push consumer related methods.

        Push consumers can only be used as async iterators
        with a context manager. This method instruments such approach.
        """

        def wrapper(
            wrapper: Any,
            _: PushConsumer,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> AsyncGenerator[Any, None]:
            return AsyncCtxManagerProxy(
                wrapper(*args, **kwargs),
                {MessagesIterator: MessagesIteratorProxy},
                self.tracer,
                capture_headers=self.capture_headers,
                capture_body=self.capture_body,
            )

        wrap_function_wrapper(
            "natsrpy._natsrpy_rs.js.consumers",
            "PushConsumer.consume",
            wrapper,
        )

    def instrument_pull(self) -> None:
        """
        Instrument pull consumer related methods.

        Pull consumer can be used directly using
        fetch method, or implicitly using an async iterator returned by consume method.

        This method instruments both of those approaches.
        """

        def consume_wrapper(
            wrapper: Any,
            _: PullConsumer,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> AsyncGenerator[Any, None]:
            return AsyncCtxManagerProxy(
                wrapper(*args, **kwargs),
                {PullConsumerFetcher: MessagesIteratorProxy},
                self.tracer,
                capture_headers=self.capture_headers,
                capture_body=self.capture_body,
            )

        async def fetch_wrapper(
            wrapper: Any,
            _: PullConsumer,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> list[JetStreamMessage]:
            messages: list[JetStreamMessage] = await wrapper(*args, **kwargs)
            if not messages:
                return messages
            links = []
            for message in messages:
                ctx = propagate.extract(message.headers)
                sc = get_current_span(ctx).get_span_context()
                links.append(Link(sc))

            span = (
                SpanBuilder(
                    self.tracer,
                    SpanKind.CONSUMER,
                    SpanAction.FETCH,
                )
                .with_links(links)
                .with_messages_count(len(messages))
                .build()
            )

            with trace.use_span(span, end_on_exit=True):
                return messages

        wrap_function_wrapper(
            "natsrpy._natsrpy_rs.js.consumers",
            "PullConsumer.fetch",
            fetch_wrapper,
        )
        wrap_function_wrapper(
            "natsrpy._natsrpy_rs.js.consumers",
            "PullConsumer.consume",
            consume_wrapper,
        )

    def instrument_message(self) -> None:
        """
        Instrumnet all methods related to a single message.

        Messages in JetStream should be acknowledged or marked as
        to be acknowledged later.

        This method wraps all of those methods into instrumented ones,
        that actually wrapped.
        """

        def gen_wrapper(action: SpanAction) -> Callable[..., Any]:
            def wrapper(
                wrapper: Any,
                message: JetStreamMessage,
                args: tuple[Any, ...],
                kwargs: dict[str, Any],
            ) -> Any:
                span = (
                    SpanBuilder(self.tracer, SpanKind.INTERNAL, action)
                    .with_js_message(
                        message,
                        capture_body=False,
                        capture_headers=False,
                    )
                    .build()
                )
                with trace.use_span(span, end_on_exit=True):
                    return wrapper(*args, **kwargs)

            return wrapper

        wrap_function_wrapper(
            "natsrpy._natsrpy_rs.js",
            "JetStreamMessage.ack",
            gen_wrapper(SpanAction.ACK),
        )
        wrap_function_wrapper(
            "natsrpy._natsrpy_rs.js",
            "JetStreamMessage.nack",
            gen_wrapper(SpanAction.NACK),
        )
        wrap_function_wrapper(
            "natsrpy._natsrpy_rs.js",
            "JetStreamMessage.progress",
            gen_wrapper(SpanAction.PROGRESS),
        )
        wrap_function_wrapper(
            "natsrpy._natsrpy_rs.js",
            "JetStreamMessage.term",
            gen_wrapper(SpanAction.TERM),
        )
        wrap_function_wrapper(
            "natsrpy._natsrpy_rs.js",
            "JetStreamMessage.next",
            gen_wrapper(SpanAction.NEXT),
        )
