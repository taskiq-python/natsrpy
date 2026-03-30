from typing import Any

from opentelemetry.semconv._incubating.attributes.messaging_attributes import (
    MESSAGING_DESTINATION_NAME,
    MESSAGING_MESSAGE_BODY_SIZE,
    MESSAGING_MESSAGE_ID,
    MESSAGING_SYSTEM,
)
from opentelemetry.trace import Span, SpanKind, Tracer
from typing_extensions import Self

from natsrpy import Message
from natsrpy.js import JetStreamMessage

DEFAULT_ATTRS = {MESSAGING_SYSTEM: "nats"}


class SpanBuilder:
    """Helper class for span creation."""

    def __init__(self, tracer: Tracer, kind: SpanKind, action: str) -> None:
        self.tracer = tracer
        self.attributes: dict[str, Any] = DEFAULT_ATTRS.copy()
        self.kind = kind
        self.action = action

    def with_subject(self, subject: str) -> Self:
        """Set message subject."""
        self.attributes[MESSAGING_DESTINATION_NAME] = subject
        return self

    def with_payload(self, payload: Any) -> Self:
        """Set payload-related attributes."""
        self.attributes[MESSAGING_MESSAGE_BODY_SIZE] = len(payload)
        return self

    def with_message_id(self, message_id: int) -> Self:
        """Set message id."""
        self.attributes[MESSAGING_MESSAGE_ID] = message_id
        return self

    def with_message(self, msg: Message) -> Self:
        """Add message-related attributes."""
        return self.with_subject(msg.subject).with_payload(msg.payload)

    def with_js_message(self, msg: JetStreamMessage) -> Self:
        """Add message-related attributes in JS context."""
        return (
            self.with_subject(msg.subject)
            .with_payload(msg.payload)
            .with_message_id(msg.stream_sequence)
        )

    def build(self) -> Span:
        """Build resulting span."""
        return self.tracer.start_span(
            self.action,
            kind=self.kind,
            attributes=self.attributes,
        )
