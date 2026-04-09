from collections.abc import Awaitable, Callable
from typing import Any

from opentelemetry import propagate, trace  # type: ignore
from opentelemetry.instrumentation.utils import is_instrumentation_enabled, unwrap
from opentelemetry.trace import SpanKind, Tracer
from wrapt import wrap_function_wrapper

from natsrpy import Nats
from natsrpy.js import JetStream

from .span_builder import SpanAction, SpanBuilder


class JSPublishInstrumentation:
    """Instrument JS publish method."""

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

    @staticmethod
    def uninstrument() -> None:
        """Remove instrumentations from core Nats."""
        unwrap(JetStream, "publish")

    def _instrument_publish(self) -> None:
        async def _wrapped_publish(
            wrapper: Callable[..., Awaitable[Any]],
            subject: str,
            payload: str | bytes | bytearray | memoryview,
            *,
            headers: dict[str, str] | None = None,
            **kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(
                    subject,
                    payload,
                    headers=headers,
                    **kwargs,
                )
            span_builder = (
                SpanBuilder(self.tracer, SpanKind.PRODUCER, SpanAction.PUBLISH)
                .with_subject(subject)
                .with_payload(payload, capture_body=self.capture_body)
            )
            headers = headers or {}
            if self.capture_headers:
                span_builder.with_headers(headers)
            span = span_builder.build()
            with trace.use_span(span, end_on_exit=True):
                propagate.inject(headers)
                return await wrapper(
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

        wrap_function_wrapper(
            "natsrpy._natsrpy_rs.js",
            "JetStream.publish",
            _publish_decorator,
        )
