from asyncio import Future
from datetime import datetime, timedelta
from typing import Any, Literal, final, overload

from . import consumers, counters, kv, managers, object_store, stream
from .managers import CountersManager, KVManager, ObjectStoreManager, StreamsManager

__all__ = [
    "JetStream",
    "JetStreamMessage",
    "Publication",
    "consumers",
    "counters",
    "kv",
    "managers",
    "object_store",
    "stream",
]

@final
class Publication:
    """Result of a JetStream publish with ``wait=True``.

    Attributes:
        stream: name of the stream the message was published to.
        sequence: sequence number assigned to the message in the stream.
        domain: JetStream domain of the stream.
        duplicate: whether the server detected this as a duplicate message.
        value: counter value. Only used if counters are enabled.
    """

    @property
    def stream(self) -> str: ...
    @property
    def sequence(self) -> int: ...
    @property
    def domain(self) -> str: ...
    @property
    def duplicate(self) -> bool: ...
    @property
    def value(self) -> str | None: ...

@final
class JetStream:
    """JetStream context for persistent messaging.

    Provides access to publish, stream management, key-value stores,
    and object stores.
    """

    @overload
    def publish(
        self,
        subject: str,
        payload: str | bytes | bytearray | memoryview,
        *,
        headers: dict[str, str] | None = None,
        err_on_disconnect: bool = False,
        wait: Literal[True],
    ) -> Future[Publication]: ...
    @overload
    def publish(
        self,
        subject: str,
        payload: str | bytes | bytearray | memoryview,
        *,
        headers: dict[str, str] | None = None,
        err_on_disconnect: bool = False,
        wait: Literal[False] = False,
    ) -> Future[None]: ...
    @overload
    def publish(
        self,
        subject: str,
        payload: str | bytes | bytearray | memoryview,
        *,
        headers: dict[str, str] | None = None,
        err_on_disconnect: bool = False,
        wait: bool = False,
    ) -> Future[Publication | None]: ...
    @property
    def kv(self) -> KVManager:
        """Manager for key-value store buckets."""

    @property
    def streams(self) -> StreamsManager:
        """Manager for JetStream streams."""

    @property
    def object_store(self) -> ObjectStoreManager:
        """Manager for object store buckets."""

    @property
    def counters(self) -> CountersManager:
        """Manager for streams with CRDT counter support."""

@final
class JetStreamMessage:
    """Message received from a JetStream consumer.

    Extends the base message with JetStream-specific metadata
    such as stream and consumer sequence numbers, delivery count,
    and acknowledgement methods.
    """

    @property
    def subject(self) -> str:
        """Subject the message was published to."""

    @property
    def reply(self) -> str | None:
        """Reply-to subject, if any."""

    @property
    def payload(self) -> bytes:
        """Message payload."""

    @property
    def headers(self) -> dict[str, Any]:
        """Message headers dictionary."""

    @property
    def domain(self) -> str | None:
        """JetStream domain, if applicable."""

    @property
    def acc_hash(self) -> str | None:
        """Account hash, if applicable."""

    @property
    def stream(self) -> str:
        """Name of the stream the message belongs to."""

    @property
    def consumer(self) -> str:
        """Name of the consumer that received the message."""

    @property
    def stream_sequence(self) -> int:
        """Sequence number of the message in the stream."""

    @property
    def consumer_sequence(self) -> int:
        """Sequence number of the message in the consumer."""

    @property
    def delivered(self) -> int:
        """Number of times this message has been delivered."""

    @property
    def pending(self) -> int:
        """Number of messages pending for the consumer."""

    @property
    def published(self) -> datetime:
        """Timestamp when the message was published."""

    @property
    def token(self) -> str | None:
        """Authentication token, if applicable."""

    def ack(self, double: bool = False) -> Future[None]:
        """Acknowledge that a message was handled.

        :param double: whether to wait for server response, defaults to False.
        """

    def nack(
        self,
        delay: float | timedelta | None = None,
        double: bool = False,
    ) -> Future[None]:
        """Negative acknowledgement.

        Signals that the message will not be processed now
        and processing can move onto the next message, NAK'd
        message will be retried.

        :param delay: delay before redelivery, defaults to None.
        :param double: whether to wait for server response, defaults to False.
        """

    def progress(self, double: bool = False) -> Future[None]:
        """Progress acknowledgement.

        Signals that the message is being handled right now.
        Sending this request before the AckWait will extend wait period
        before redelivering a message.

        :param double: whether to wait for server response, defaults to False.
        """

    def next(self, double: bool = False) -> Future[None]:
        """Next acknowledgement.

        Only applies to pull consumers.
        Acknowledges message processing and instructs server to send
        delivery of the next message to the reply subject.

        :param double: whether to wait for server response, defaults to False.
        """

    def term(self, double: bool = False) -> Future[None]:
        """Term acknowledgement.

        Instructs server to stop redelivering message.
        Useful to stop redelivering a message after multiple NACKs.

        :param double: whether to wait for server response, defaults to False.
        """
