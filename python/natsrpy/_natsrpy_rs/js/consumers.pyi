from asyncio import Future
from datetime import timedelta
from typing import final

from natsrpy._natsrpy_rs.js import JetStreamMessage
from typing_extensions import Self

__all__ = [
    "AckPolicy",
    "DeliverPolicy",
    "MessagesIterator",
    "PriorityPolicy",
    "PullConsumer",
    "PullConsumerConfig",
    "PushConsumer",
    "PushConsumerConfig",
    "ReplayPolicy",
]

@final
class DeliverPolicy:
    """Policy controlling which messages a consumer starts receiving.

    Attributes:
        ALL: deliver all available messages.
        LAST: deliver starting with the last message.
        NEW: deliver only new messages.
        BY_START_SEQUENCE: deliver from a specific sequence number.
        BY_START_TIME: deliver from a specific timestamp.
        LAST_PER_SUBJECT: deliver the last message for each subject.
    """

    ALL: DeliverPolicy
    LAST: DeliverPolicy
    NEW: DeliverPolicy
    BY_START_SEQUENCE: DeliverPolicy
    BY_START_TIME: DeliverPolicy
    LAST_PER_SUBJECT: DeliverPolicy

@final
class AckPolicy:
    """Acknowledgement policy for a consumer.

    Attributes:
        EXPLICIT: each message must be individually acknowledged.
        NONE: no acknowledgement required.
        ALL: acknowledging a message implicitly acknowledges all prior
            messages.
    """

    EXPLICIT: AckPolicy
    NONE: AckPolicy
    ALL: AckPolicy

@final
class ReplayPolicy:
    """Replay speed policy for a consumer.

    Attributes:
        INSTANT: deliver messages as fast as possible.
        ORIGINAL: deliver messages at the rate they were originally
            published.
    """

    INSTANT: ReplayPolicy
    ORIGINAL: ReplayPolicy

@final
class PriorityPolicy:
    """Priority dispatch policy for a consumer.

    Attributes:
        NONE: no priority dispatching.
        OVERFLOW: dispatch to priority groups on overflow.
        PINNED_CLIENT: pin messages to a specific client.
        PRIORITIZED: dispatch based on message priority.
    """

    NONE: PriorityPolicy
    OVERFLOW: PriorityPolicy
    PINNED_CLIENT: PriorityPolicy
    PRIORITIZED: PriorityPolicy

@final
class PullConsumerConfig:
    """Configuration for a pull-based JetStream consumer.

    Attributes:
        name: consumer name.
        durable_name: durable consumer name for persistence across restarts.
        description: human-readable consumer description.
        deliver_policy: policy for initial message delivery.
        delivery_start_sequence: starting sequence when using
            ``BY_START_SEQUENCE`` deliver policy.
        delivery_start_time: starting timestamp when using
            ``BY_START_TIME`` deliver policy.
        ack_policy: acknowledgement policy.
        ack_wait: how long the server waits for an acknowledgement.
        max_deliver: maximum number of delivery attempts per message.
        filter_subject: subject filter for the consumer.
        filter_subjects: list of subject filters for the consumer.
        replay_policy: message replay speed policy.
        rate_limit: rate limit in bits per second.
        sample_frequency: percentage of acknowledgements to sample.
        max_waiting: maximum pull requests waiting to be fulfilled.
        max_ack_pending: maximum outstanding unacknowledged messages.
        headers_only: when True, deliver only message headers.
        max_batch: maximum messages per pull batch.
        max_bytes: maximum bytes per pull batch.
        max_expires: maximum pull request expiration duration.
        inactive_threshold: duration before an inactive consumer is
            removed.
        num_replicas: number of consumer replicas.
        memory_storage: when True, use in-memory storage.
        metadata: custom key-value metadata.
        backoff: list of durations for redelivery backoff.
        priority_policy: priority dispatch policy.
        priority_groups: list of priority group names.
        pause_until: timestamp until which the consumer is paused.
    """

    name: str | None
    durable_name: str | None
    description: str | None
    deliver_policy: DeliverPolicy
    delivery_start_sequence: int | None
    delivery_start_time: int | None
    ack_policy: AckPolicy
    ack_wait: timedelta
    max_deliver: int
    filter_subject: str
    filter_subjects: list[str]
    replay_policy: ReplayPolicy
    rate_limit: int
    sample_frequency: int
    max_waiting: int
    max_ack_pending: int
    headers_only: bool
    max_batch: int
    max_bytes: int
    max_expires: timedelta
    inactive_threshold: timedelta
    num_replicas: int
    memory_storage: bool
    metadata: dict[str, str]
    backoff: list[timedelta]
    priority_policy: PriorityPolicy
    priority_groups: list[str]
    pause_until: int | None

    def __new__(
        cls,
        name: str | None = None,
        durable_name: str | None = None,
        description: str | None = None,
        deliver_policy: DeliverPolicy | None = None,
        delivery_start_sequence: int | None = None,
        delivery_start_time: int | None = None,
        ack_policy: AckPolicy | None = None,
        ack_wait: float | timedelta | None = None,
        max_deliver: int | None = None,
        filter_subject: str | None = None,
        filter_subjects: list[str] | None = None,
        replay_policy: ReplayPolicy | None = None,
        rate_limit: int | None = None,
        sample_frequency: int | None = None,
        max_waiting: int | None = None,
        max_ack_pending: int | None = None,
        headers_only: bool | None = None,
        max_batch: int | None = None,
        max_bytes: int | None = None,
        max_expires: float | timedelta | None = None,
        inactive_threshold: float | timedelta | None = None,
        num_replicas: int | None = None,
        memory_storage: bool | None = None,
        metadata: dict[str, str] | None = None,
        backoff: list[float | timedelta] | None = None,
        priority_policy: PriorityPolicy | None = None,
        priority_groups: list[str] | None = None,
        pause_until: int | None = None,
    ) -> Self: ...

@final
class PushConsumerConfig:
    """Configuration for a push-based JetStream consumer.

    Attributes:
        deliver_subject: subject where messages are pushed to.
        name: consumer name.
        durable_name: durable consumer name for persistence across restarts.
        description: human-readable consumer description.
        deliver_group: queue group for load-balanced delivery.
        deliver_policy: policy for initial message delivery.
        delivery_start_sequence: starting sequence when using
            ``BY_START_SEQUENCE`` deliver policy.
        delivery_start_time: starting timestamp when using
            ``BY_START_TIME`` deliver policy.
        ack_policy: acknowledgement policy.
        ack_wait: how long the server waits for an acknowledgement.
        max_deliver: maximum number of delivery attempts per message.
        filter_subject: subject filter for the consumer.
        filter_subjects: list of subject filters for the consumer.
        replay_policy: message replay speed policy.
        rate_limit: rate limit in bits per second.
        sample_frequency: percentage of acknowledgements to sample.
        max_waiting: maximum pull requests waiting to be fulfilled.
        max_ack_pending: maximum outstanding unacknowledged messages.
        headers_only: when True, deliver only message headers.
        flow_control: when True, enable flow control.
        idle_heartbeat: interval for idle heartbeat messages.
        num_replicas: number of consumer replicas.
        memory_storage: when True, use in-memory storage.
        metadata: custom key-value metadata.
        backoff: list of durations for redelivery backoff.
        inactive_threshold: duration before an inactive consumer is
            removed.
        pause_until: timestamp until which the consumer is paused.
    """

    deliver_subject: str
    name: str | None
    durable_name: str | None
    description: str | None
    deliver_group: str | None
    deliver_policy: DeliverPolicy
    delivery_start_sequence: int | None
    delivery_start_time: int | None
    ack_policy: AckPolicy
    ack_wait: timedelta
    max_deliver: int
    filter_subject: str
    filter_subjects: list[str]
    replay_policy: ReplayPolicy
    rate_limit: int
    sample_frequency: int
    max_waiting: int
    max_ack_pending: int
    headers_only: bool
    flow_control: bool
    idle_heartbeat: timedelta
    num_replicas: int
    memory_storage: bool
    metadata: dict[str, str]
    backoff: list[timedelta]
    inactive_threshold: timedelta
    pause_until: int | None

    def __new__(
        cls,
        deliver_subject: str,
        name: str | None = None,
        durable_name: str | None = None,
        description: str | None = None,
        deliver_group: str | None = None,
        deliver_policy: DeliverPolicy | None = None,
        delivery_start_sequence: int | None = None,
        delivery_start_time: int | None = None,
        ack_policy: AckPolicy | None = None,
        ack_wait: float | timedelta | None = None,
        max_deliver: int | None = None,
        filter_subject: str | None = None,
        filter_subjects: list[str] | None = None,
        replay_policy: ReplayPolicy | None = None,
        rate_limit: int | None = None,
        sample_frequency: int | None = None,
        max_waiting: int | None = None,
        max_ack_pending: int | None = None,
        headers_only: bool | None = None,
        flow_control: bool | None = None,
        idle_heartbeat: float | timedelta | None = None,
        num_replicas: int | None = None,
        memory_storage: bool | None = None,
        metadata: dict[str, str] | None = None,
        backoff: list[float | timedelta] | None = None,
        inactive_threshold: float | timedelta | None = None,
        pause_until: int | None = None,
    ) -> Self: ...

@final
class MessagesIterator:
    """Async iterator over JetStream consumer messages."""

    def __aiter__(self) -> Self: ...
    def __anext__(self) -> Future[JetStreamMessage]: ...
    def next(
        self,
        timeout: float | timedelta | None = None,
    ) -> Future[JetStreamMessage]:
        """Receive the next message from the consumer.

        :param timeout: maximum time to wait in seconds or as a timedelta,
            defaults to None (wait indefinitely).
        :return: the next JetStream message.
        """

@final
class PushConsumer:
    """A push-based JetStream consumer.

    Messages are delivered by the server to a specified subject.
    """

    @property
    def name(self) -> str:
        """Get consumer name."""

    @property
    def stream_name(self) -> str:
        """Get stream name that this consumer attached to."""

    def messages(self) -> Future[MessagesIterator]:
        """Get an async iterator for consuming messages.

        :return: an async iterator over JetStream messages.
        """

@final
class PullConsumer:
    """A pull-based JetStream consumer.

    Messages are fetched on demand in batches by the client.
    """

    @property
    def name(self) -> str:
        """Get consumer name."""

    @property
    def stream_name(self) -> str:
        """Get stream name that this consumer attached to."""

    def fetch(
        self,
        max_messages: int | None = None,
        group: str | None = None,
        priority: int | None = None,
        max_bytes: int | None = None,
        heartbeat: float | timedelta | None = None,
        expires: float | timedelta | None = None,
        min_pending: int | None = None,
        min_ack_pending: int | None = None,
        timeout: float | timedelta | None = None,
    ) -> Future[list[JetStreamMessage]]:
        """Fetch a batch of messages from the consumer.

        :param max_messages: maximum number of messages to fetch.
        :param group: consumer group for priority dispatch.
        :param priority: priority level for the fetch request.
        :param max_bytes: maximum total bytes to fetch.
        :param heartbeat: server heartbeat interval in seconds or as a
            timedelta.
        :param expires: fetch request expiration in seconds or as a
            timedelta.
        :param min_pending: minimum pending messages before pausing.
        :param min_ack_pending: minimum unacknowledged messages before
            pausing.
        :param timeout: overall operation timeout in seconds or as a
            timedelta.
        :return: list of fetched messages.
        """
