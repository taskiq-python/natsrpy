from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AbstractContextManager
from contextvars import Token
from functools import wraps
from typing import Any

from opentelemetry import context, propagate, trace
from opentelemetry.instrumentation.utils import is_instrumentation_enabled, unwrap
from opentelemetry.trace import SpanKind, Tracer
from wrapt import wrap_function_wrapper

from natsrpy import IteratorSubscription, Message, Nats

from .span_builder import SpanBuilder


def _cleanup_otel_context(
    token: Token[Any] | None,
    span_manager: AbstractContextManager[Any] | None,
) -> None:
    """Detach the current OTel context and end the active span, if any."""
    if token:
        context.detach(token)
    if span_manager:
        span_manager.__exit__(None, None, None)


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
        self._instrument_iter_subscription()
        self._instrument_cb_subscription()

    @staticmethod
    def uninstrument() -> None:
        """Remove instrumentations from core Nats."""
        unwrap(Nats, "publish")
        unwrap(IteratorSubscription, "__aiter__")

    def _instrument_publish(self) -> None:
        def _wrapped_publish(
            wrapper: Callable[..., Any],
            subject: str,
            payload: bytes | str | bytearray | memoryview,
            *,
            headers: dict[str, Any] | None = None,
            **kwargs: dict[str, Any],
        ) -> Any:
            span = (
                SpanBuilder(self.tracer, SpanKind.PRODUCER, "publish")
                .with_subject(subject)
                .with_payload(payload)
                .build()
            )
            if not span:
                return wrapper(
                    subject,
                    payload,
                    headers=headers,
                    **kwargs,
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

    def _instrument_iter_subscription(self) -> None:

        async def _instrumented_iter(
            sub: IteratorSubscription,
        ) -> AsyncIterator[Message]:
            """Async generator wrapping an iterator subscription with OTel context.

            Each ``async for`` loop gets its own generator instance with
            independent context state.  The ``finally`` block guarantees
            cleanup when the loop exits — whether via ``break``, an
            exception, or normal ``StopAsyncIteration``.
            """
            token: Token[Any] | None = None
            span_manager: AbstractContextManager[Any] | None = None
            try:
                while True:
                    # Clean up the *previous* iteration's context before
                    # waiting for the next message.
                    _cleanup_otel_context(token, span_manager)
                    token = None
                    span_manager = None

                    try:
                        msg = await IteratorSubscription.__anext__(sub)
                    except StopAsyncIteration:
                        return

                    if not is_instrumentation_enabled():
                        yield msg
                        continue

                    ctx = propagate.extract(msg.headers)
                    token = context.attach(ctx)
                    span = (
                        SpanBuilder(self.tracer, SpanKind.CONSUMER, "receive")
                        .with_message(msg)
                        .build()
                    )
                    if span:
                        span_manager = trace.use_span(span, end_on_exit=True)
                        span_manager.__enter__()
                    yield msg
            finally:
                _cleanup_otel_context(token, span_manager)

        def _custom_aiter(
            wrapper: Any,
            instance: IteratorSubscription,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> AsyncIterator[Message]:
            return _instrumented_iter(instance)

        wrap_function_wrapper(
            "natsrpy._natsrpy_rs",
            "IteratorSubscription.__aiter__",
            _custom_aiter,
        )

    def _instrument_cb_subscription(self) -> None:
        """Instrument callback subscriptions."""

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
                    SpanBuilder(self.tracer, SpanKind.CONSUMER, "receive")
                    .with_message(message)
                    .build()
                )
                try:
                    with trace.use_span(span, end_on_exit=True):
                        await cb(message)
                finally:
                    context.detach(token)

            return _fixed_cb

        def _custom_subscribe(
            wrapper: Any,
            _: Nats,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            """
            Wrapper around subscribe method.

            This wrapper substitutes subscribe
            method. This method replaces
            `Nats`.`subscribe` method.

            This method parses arguments passed to subscribe method
            and wraps callback function with a decorator.
            """

            def process_args(
                subject: str,
                callback: Callable[[Message], Awaitable[None]] | None = None,
                queue: str | None = None,
            ) -> tuple[Any, ...]:
                if callback:
                    callback = callback_wrapper(callback)
                return (subject, callback, queue)

            return wrapper(*process_args(*args, **kwargs))

        wrap_function_wrapper(
            "natsrpy._natsrpy_rs",
            "Nats.subscribe",
            _custom_subscribe,
        )
