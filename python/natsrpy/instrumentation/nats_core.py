from collections.abc import AsyncGenerator, Awaitable, Callable
from functools import wraps
from types import TracebackType
from typing import Any

from opentelemetry import context, propagate, trace
from opentelemetry.instrumentation.utils import is_instrumentation_enabled, unwrap
from opentelemetry.trace import SpanKind, Tracer
from typing_extensions import Self
from wrapt import ObjectProxy, wrap_function_wrapper

from natsrpy import IteratorSubscription, Message, Nats

from .span_builder import SpanAction, SpanBuilder


class IterableSubscriptionProxy(ObjectProxy):  # type: ignore
    """Proxy for iterable subscriptions."""

    def __init__(self, wrapped: IteratorSubscription, tracer: Tracer) -> None:
        super().__init__(wrapped)
        # Proxy-local attrs should have _self_ prefix
        self._self_tracer = tracer
        self._self_cancel_ctx: tuple[Any, Any] | None = None

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
        next_msg: Message = await anext(self.__wrapped__)
        if not is_instrumentation_enabled():
            return next_msg
        new_ctx = propagate.extract(next_msg.headers)
        token = context.attach(new_ctx)
        span = (
            SpanBuilder(self._self_tracer, SpanKind.CONSUMER, SpanAction.RECEIVE)
            .with_message(next_msg)
            .build()
        )
        span_ctx = trace.use_span(span, end_on_exit=True)
        span_ctx.__enter__()
        self._self_cancel_ctx = (token, span_ctx)

        return next_msg


class SubscriptionCtxProxy(ObjectProxy):  # type: ignore
    """Proxy object for subscription context manager."""

    def __init__(self, wrapped: Any, tracer: Tracer) -> None:
        super().__init__(wrapped)
        self._self_tracer = tracer
        self._self_sub = None

    async def __aenter__(self) -> Any:
        sub = await self.__wrapped__.__aenter__()
        if isinstance(sub, IteratorSubscription):
            sub = IterableSubscriptionProxy(sub, self._self_tracer)
        self._self_sub = sub
        return sub

    def __aexit__(self, *args: Any, **kwargs: dict[Any, Any]) -> Any:
        if self._self_sub and isinstance(self._self_sub, IterableSubscriptionProxy):
            self._self_sub.__cancel_ctx__(*args, **kwargs)


class NatsCoreInstrumentator:
    """Instrument core nats methods."""

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
        """Setup otel instrumentation for core Nats."""
        self._instrument_publish()
        self._instrument_subscriptions()

    @staticmethod
    def uninstrument() -> None:
        """Remove instrumentations from core Nats."""
        unwrap(Nats, "publish")

    def _instrument_publish(self) -> None:
        def _wrapped_publish(
            wrapper: Callable[..., Any],
            subject: str,
            payload: bytes | str | bytearray | memoryview,
            *,
            headers: dict[str, Any] | None = None,
            **kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return wrapper(
                    subject,
                    payload,
                    headers=headers,
                    **kwargs,
                )
            span = (
                SpanBuilder(self.tracer, SpanKind.PRODUCER, SpanAction.PUBLISH)
                .with_subject(subject)
                .with_payload(payload)
                .build()
            )
            headers = headers or {}
            with trace.use_span(span, end_on_exit=True):
                propagate.inject(headers)
                return wrapper(
                    subject,
                    payload,
                    headers=headers,
                    **kwargs,
                )

        def _publish_decorator(
            wrapper: Any,
            _: Nats,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped_publish(wrapper, *args, **kwargs)

        wrap_function_wrapper("natsrpy._natsrpy_rs", "Nats.publish", _publish_decorator)

    def _instrument_subscriptions(self) -> None:
        """Create instrumentation for."""

        def callback_wrapper(
            cb: Callable[[Message], Awaitable[None]],
        ) -> Callable[[Message], Awaitable[None]]:
            """
            Custom decorator around callback functions.

            Generated callback creates span on message
            receive and ends span when callback function finishes.
            """

            @wraps(cb)
            async def _fixed_cb(message: Message) -> None:
                """Fixed callback function."""
                if not is_instrumentation_enabled():
                    await cb(message)
                ctx = propagate.extract(message.headers)
                token = context.attach(ctx)
                span = (
                    SpanBuilder(self.tracer, SpanKind.CONSUMER, SpanAction.RECEIVE)
                    .with_message(message)
                    .build()
                )
                try:
                    with trace.use_span(span, end_on_exit=True):
                        await cb(message)
                finally:
                    context.detach(token)

            return _fixed_cb

        def process_args(
            subject: str,
            callback: Callable[[Message], Awaitable[None]] | None = None,
            queue: str | None = None,
        ) -> tuple[Any, ...]:
            """Function to wrap callback when it's passed as subscribe argument."""
            if callback:
                callback = callback_wrapper(callback)
            return (subject, callback, queue)

        def wrapper(
            wrapper: Any,
            _: Nats,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> AsyncGenerator[Any, None]:
            return SubscriptionCtxProxy(
                wrapper(*process_args(*args, **kwargs)),
                self.tracer,
            )

        wrap_function_wrapper("natsrpy._natsrpy_rs", "Nats.subscribe", wrapper)
