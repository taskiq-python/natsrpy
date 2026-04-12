import enum
from collections.abc import Sequence
from typing import Any

from opentelemetry.semconv._incubating.attributes.messaging_attributes import (
    MESSAGING_BATCH_MESSAGE_COUNT,
    MESSAGING_DESTINATION_NAME,
    MESSAGING_MESSAGE_BODY_SIZE,
    MESSAGING_MESSAGE_ID,
    MESSAGING_SYSTEM,
)
from opentelemetry.trace import Link, Span, SpanKind, Tracer
from typing_extensions import Self

from natsrpy import Message
from natsrpy.js import JetStreamMessage

DEFAULT_ATTRS = {MESSAGING_SYSTEM: "nats"}


@enum.unique
class SpanAction(enum.Enum):
    """Available span actions."""

    PUBLISH = "publish"
    RECEIVE = "receive"
    FETCH = "fetch"
    ACK = "ack"
    NACK = "nack"
    PROGRESS = "progress"
    TERM = "term"
    NEXT = "next"
    # KeyValue operations
    KV_GET = "kv.get"
    KV_PUT = "kv.put"
    KV_CREATE = "kv.create"
    KV_UPDATE = "kv.update"
    KV_DELETE = "kv.delete"
    KV_PURGE = "kv.purge"
    KV_WATCH = "kv.watch"
    KV_KEYS = "kv.keys"
    KV_HISTORY = "kv.history"
    KV_ENTRY = "kv.entry"
    # ObjectStore operations
    OBJ_PUT = "obj.put"
    OBJ_GET = "obj.get"
    OBJ_DELETE = "obj.delete"
    OBJ_SEAL = "obj.seal"
    OBJ_INFO = "obj.info"
    OBJ_WATCH = "obj.watch"
    OBJ_LIST = "obj.list"
    OBJ_LINK = "obj.link"
    OBJ_UPDATE_METADATA = "obj.update_metadata"


class SpanBuilder:
    """Helper class for span creation."""

    def __init__(self, tracer: Tracer, kind: SpanKind, action: SpanAction) -> None:
        self.tracer = tracer
        self.attributes: dict[str, Any] = DEFAULT_ATTRS.copy()
        self.kind = kind
        self.action = action
        self.links: Sequence[Link] | None = None

    def with_subject(self, subject: str) -> Self:
        """Set message subject."""
        self.attributes[MESSAGING_DESTINATION_NAME] = subject
        return self

    def with_payload(self, payload: Any, capture_body: bool = False) -> Self:
        """Set payload-related attributes."""
        self.attributes[MESSAGING_MESSAGE_BODY_SIZE] = len(payload)
        if capture_body:
            self.attributes["messaging.message.payload"] = payload
        return self

    def with_headers(self, headers: dict[str, Any]) -> Self:
        """Add headers to a list of lables."""
        self.attributes["messaging.message.headers"] = headers
        return self

    def with_message_id(self, message_id: int) -> Self:
        """Set message id."""
        self.attributes[MESSAGING_MESSAGE_ID] = message_id
        return self

    def with_message(
        self,
        msg: Message,
        capture_body: bool,
        capture_headers: bool,
    ) -> Self:
        """Add message-related attributes."""
        self.with_subject(msg.subject).with_payload(
            msg.payload,
            capture_body=capture_body,
        )
        if capture_headers:
            self.with_headers(msg.headers)
        return self

    def with_messages_count(self, count: int) -> Self:
        """Set number of messages in the batch."""
        self.attributes[MESSAGING_BATCH_MESSAGE_COUNT] = count
        return self

    def with_js_message(
        self,
        msg: JetStreamMessage,
        capture_body: bool,
        capture_headers: bool,
    ) -> Self:
        """Add message-related attributes in JS context."""
        (
            self.with_subject(msg.subject)
            .with_payload(msg.payload, capture_body=capture_body)
            .with_message_id(msg.stream_sequence)
        )
        if capture_headers:
            self.with_headers(msg.headers)
        return self

    def with_kv_bucket(self, bucket: str) -> Self:
        """Set key-value bucket name."""
        self.attributes[MESSAGING_DESTINATION_NAME] = bucket
        self.attributes["nats.kv.bucket"] = bucket
        return self

    def with_kv_key(self, key: str) -> Self:
        """Set key-value entry key."""
        self.attributes["nats.kv.key"] = key
        return self

    def with_kv_value(self, value: bytes | str, capture_body: bool = False) -> Self:
        """Set key-value entry value attributes."""
        self.attributes[MESSAGING_MESSAGE_BODY_SIZE] = len(value)
        if capture_body:
            self.attributes["nats.kv.value"] = value
        return self

    def with_object_name(self, name: str) -> Self:
        """Set object store object name."""
        self.attributes[MESSAGING_DESTINATION_NAME] = name
        self.attributes["nats.object_store.name"] = name
        return self

    def with_object_size(self, size: int) -> Self:
        """Set object size in bytes."""
        self.attributes[MESSAGING_MESSAGE_BODY_SIZE] = size
        return self

    def with_links(self, links: Sequence[Link]) -> Self:
        """Attache linked spans."""
        self.links = links
        return self

    def build(self) -> Span:
        """Build resulting span."""
        return self.tracer.start_span(
            self.action.value.lower(),
            kind=self.kind,
            attributes=self.attributes,
            links=self.links,
        )
