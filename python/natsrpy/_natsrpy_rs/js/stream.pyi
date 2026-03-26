from asyncio import Future
from datetime import datetime, timedelta
from typing import Any, final

from typing_extensions import Self

from .managers import ConsumersManager

__all__ = [
    "ClusterInfo",
    "Compression",
    "ConsumerLimits",
    "DiscardPolicy",
    "External",
    "PeerInfo",
    "PersistenceMode",
    "Placement",
    "Republish",
    "RetentionPolicy",
    "Source",
    "SourceInfo",
    "StorageType",
    "Stream",
    "StreamConfig",
    "StreamInfo",
    "StreamMessage",
    "StreamState",
    "SubjectTransform",
]

@final
class StorageType:
    """Stream storage backend type.

    Attributes:
        FILE: persistent file-based storage.
        MEMORY: in-memory storage.
    """

    FILE: StorageType
    MEMORY: StorageType

@final
class DiscardPolicy:
    """Policy for discarding messages when stream limits are reached.

    Attributes:
        OLD: discard the oldest messages first.
        NEW: reject new messages when the limit is reached.
    """

    OLD: DiscardPolicy
    NEW: DiscardPolicy

@final
class RetentionPolicy:
    """Stream message retention policy.

    Attributes:
        LIMITS: retain messages until size or age limits are hit.
        INTEREST: retain messages until all known consumers have acknowledged.
        WORKQUEUE: retain messages until acknowledged by a single consumer.
    """

    LIMITS: RetentionPolicy
    INTEREST: RetentionPolicy
    WORKQUEUE: RetentionPolicy

@final
class Compression:
    """Stream data compression algorithm.

    Attributes:
        S2: S2 compression.
        NONE: no compression.
    """

    S2: Compression
    NONE: Compression

@final
class PersistenceMode:
    """Write persistence mode for stream messages.

    Attributes:
        Default: synchronous write to disk.
        Async: asynchronous write to disk.
    """

    Default: PersistenceMode
    Async: PersistenceMode

@final
class ConsumerLimits:
    """Default consumer limits applied to consumers on this stream.

    Attributes:
        inactive_threshold: duration after which an inactive consumer
            is removed.
        max_ack_pending: maximum number of outstanding unacknowledged
            messages.
    """

    inactive_threshold: timedelta
    max_ack_pending: int

    def __new__(cls, inactive_threshold: timedelta, max_ack_pending: int) -> Self: ...

@final
class External:
    """External stream reference for cross-account or cross-domain access.

    Attributes:
        api_prefix: API prefix for the external stream.
        delivery_prefix: optional delivery prefix override.
    """

    api_prefix: str
    delivery_prefix: str | None

    def __new__(cls, api_prefix: str, delivery_prefix: str | None = None) -> Self: ...

@final
class SubjectTransform:
    """Subject mapping transformation rule.

    Attributes:
        source: source subject pattern.
        destination: destination subject pattern.
    """

    source: str
    destination: str

    def __new__(cls, source: str, destination: str) -> Self: ...

@final
class Source:
    """Configuration for a stream source or mirror origin.

    Attributes:
        name: name of the source stream.
        filter_subject: optional subject filter applied to the source.
        external: optional external stream reference.
        start_sequence: optional starting sequence number.
        start_time: optional starting timestamp.
        domain: optional JetStream domain.
        subject_transforms: optional subject transformation rule.
    """

    name: str
    filter_subject: str | None = None
    external: External | None = None
    start_sequence: int | None = None
    start_time: int | None = None
    domain: str | None = None
    subject_transforms: SubjectTransform | None = None

    def __new__(
        cls,
        name: str,
        filter_subject: str | None = None,
        external: External | None = None,
        start_sequence: int | None = None,
        start_time: int | None = None,
        domain: str | None = None,
        subject_transforms: SubjectTransform | None = None,
    ) -> Self: ...

@final
class Placement:
    """Placement hints for stream replicas across clusters and tags.

    Attributes:
        cluster: preferred cluster name.
        tags: server tags used for placement.
    """

    cluster: str | None
    tags: list[str] | None

    def __new__(
        cls,
        cluster: str | None = None,
        tags: list[str] | None = None,
    ) -> Self: ...

@final
class Republish:
    """Republish configuration for echoing stream messages to other subjects.

    Attributes:
        source: source subject filter.
        destination: destination subject to republish to.
        headers_only: when True, only headers are republished.
    """

    source: str
    destination: str
    headers_only: bool

    def __new__(cls, source: str, destination: str, headers_only: bool) -> Self: ...

@final
class StreamConfig:
    """Configuration for creating or updating a JetStream stream.

    Attributes:
        name: stream name.
        subjects: list of subjects the stream listens on.
        max_bytes: maximum total size of the stream in bytes.
        max_messages: maximum number of messages in the stream.
        max_messages_per_subject: maximum messages per subject.
        discard: policy for discarding messages when limits are reached.
        discard_new_per_subject: when True, apply discard policy per
            subject.
        retention: message retention policy.
        max_consumers: maximum number of consumers.
        max_age: maximum message age.
        max_message_size: maximum size of a single message in bytes.
        storage: storage backend type.
        num_replicas: number of stream replicas.
        no_ack: when True, disable publish acknowledgements.
        duplicate_window: time window for duplicate detection.
        template_owner: name of the owning stream template.
        sealed: when True, the stream is read-only.
        description: human-readable stream description.
        allow_rollup: when True, allow ``Nats-Rollup`` header to purge
            subjects.
        deny_delete: when True, deny message deletion via the API.
        deny_purge: when True, deny stream purge via the API.
        republish: configuration for republishing messages.
        allow_direct: when True, enable direct get API for the stream.
        mirror_direct: when True, enable direct get for mirror streams.
        mirror: source configuration when the stream is a mirror.
        sources: list of source configurations for aggregate streams.
        metadata: custom key-value metadata.
        subject_transform: subject transformation rule.
        compression: compression algorithm for stored messages.
        consumer_limits: default limits applied to new consumers.
        first_sequence: initial sequence number for the stream.
        placement: cluster and tag placement hints.
        persist_mode: write persistence mode.
        pause_until: timestamp until which the stream is paused.
        allow_message_ttl: when True, allow per-message TTL.
        subject_delete_marker_ttl: TTL for subject delete markers.
        allow_atomic_publish: when True, enable atomic multi-message
            publish.
        allow_message_schedules: when True, enable scheduled message
            delivery.
        allow_message_counter: when True, enable message counter header.
    """

    name: str
    subjects: list[str]
    max_bytes: int | None
    max_messages: int | None
    max_messages_per_subject: int | None
    discard: DiscardPolicy | None
    discard_new_per_subject: bool | None
    retention: RetentionPolicy | None
    max_consumers: int | None
    max_age: timedelta | None
    max_message_size: int | None
    storage: StorageType | None
    num_replicas: int | None
    no_ack: bool | None
    duplicate_window: timedelta | None
    template_owner: str | None
    sealed: bool | None
    description: str | None
    allow_rollup: bool | None
    deny_delete: bool | None
    deny_purge: bool | None
    republish: Republish | None
    allow_direct: bool | None
    mirror_direct: bool | None
    mirror: Source | None
    sources: list[Source] | None
    metadata: dict[str, str] | None
    subject_transform: SubjectTransform | None
    compression: Compression | None
    consumer_limits: ConsumerLimits | None
    first_sequence: int | None
    placement: Placement | None
    persist_mode: PersistenceMode | None
    pause_until: int | None
    allow_message_ttl: bool | None
    subject_delete_marker_ttl: timedelta | None
    allow_atomic_publish: bool | None
    allow_message_schedules: bool | None
    allow_message_counter: bool | None

    def __new__(
        cls,
        name: str,
        subjects: list[str],
        max_bytes: int | None = None,
        max_messages: int | None = None,
        max_messages_per_subject: int | None = None,
        discard: DiscardPolicy | None = None,
        discard_new_per_subject: bool | None = None,
        retention: RetentionPolicy | None = None,
        max_consumers: int | None = None,
        max_age: float | timedelta | None = None,
        max_message_size: int | None = None,
        storage: StorageType | None = None,
        num_replicas: int | None = None,
        no_ack: bool | None = None,
        duplicate_window: float | timedelta | None = None,
        template_owner: str | None = None,
        sealed: bool | None = None,
        description: str | None = None,
        allow_rollup: bool | None = None,
        deny_delete: bool | None = None,
        deny_purge: bool | None = None,
        republish: Republish | None = None,
        allow_direct: bool | None = None,
        mirror_direct: bool | None = None,
        mirror: Source | None = None,
        sources: list[Source] | None = None,
        metadata: dict[str, str] | None = None,
        subject_transform: SubjectTransform | None = None,
        compression: Compression | None = None,
        consumer_limits: ConsumerLimits | None = None,
        first_sequence: int | None = None,
        placement: Placement | None = None,
        persist_mode: PersistenceMode | None = None,
        pause_until: int | None = None,
        allow_message_ttl: bool | None = None,
        subject_delete_marker_ttl: float | timedelta | None = None,
        allow_atomic_publish: bool | None = None,
        allow_message_schedules: bool | None = None,
        allow_message_counter: bool | None = None,
    ) -> Self: ...

@final
class StreamMessage:
    """A raw message stored in a JetStream stream.

    Attributes:
        subject: subject the message was published to.
        sequence: sequence number of the message.
        headers: message headers dictionary.
        payload: message payload.
        time: timestamp when the message was stored.
    """

    subject: str
    sequence: int
    headers: dict[str, Any]
    payload: bytes
    time: datetime

@final
class StreamState:
    """Current state snapshot of a JetStream stream.

    Attributes:
        messages: total number of messages in the stream.
        bytes: total size of the stream in bytes.
        first_sequence: sequence number of the first message.
        first_timestamp: timestamp of the first message.
        last_sequence: sequence number of the last message.
        last_timestamp: timestamp of the last message.
        consumer_count: number of consumers bound to the stream.
        subjects_count: number of unique subjects in the stream.
        deleted_count: number of deleted messages, if available.
        deleted: list of deleted sequence numbers, if available.
    """

    messages: int
    bytes: int
    first_sequence: int
    first_timestamp: int
    last_sequence: int
    last_timestamp: int
    consumer_count: int
    subjects_count: int
    deleted_count: int | None
    deleted: list[int] | None

@final
class SourceInfo:
    """Runtime information about a stream source.

    Attributes:
        name: name of the source stream.
        lag: number of messages the source is behind.
        active: duration since the last activity.
        filter_subject: subject filter applied to the source.
        subject_transform_dest: destination of the subject transform.
        subject_transforms: list of subject transformation rules.
    """

    name: str
    lag: int
    active: timedelta | None
    filter_subject: str | None
    subject_transform_dest: str | None
    subject_transforms: list[SubjectTransform]

@final
class PeerInfo:
    """Information about a stream cluster peer.

    Attributes:
        name: name of the peer server.
        current: whether the peer is up to date.
        active: duration since the last peer activity.
        offline: whether the peer is offline.
        lag: number of messages the peer is behind, if known.
    """

    name: str
    current: bool
    active: timedelta
    offline: bool
    lag: int | None

@final
class ClusterInfo:
    """Cluster information for a JetStream stream.

    Attributes:
        name: cluster name.
        raft_group: Raft group name for the stream.
        leader: name of the current leader server.
        leader_since: timestamp when the current leader was elected.
        system_account: whether this belongs to the system account.
        traffic_account: traffic accounting identifier.
        replicas: list of peer replicas.
    """

    name: str | None
    raft_group: str | None
    leader: str | None
    leader_since: int | None
    system_account: bool
    traffic_account: str | None
    replicas: list[PeerInfo]

@final
class StreamInfo:
    """Detailed information about a JetStream stream.

    Attributes:
        config: stream configuration.
        created: timestamp when the stream was created.
        state: current stream state.
        cluster: cluster information, if applicable.
        mirror: mirror source info, if the stream is a mirror.
        sources: list of source info for aggregate streams.
    """

    config: StreamConfig
    created: float
    state: StreamState
    cluster: ClusterInfo | None
    mirror: SourceInfo | None
    sources: list[SourceInfo]

@final
class Stream:
    """A JetStream stream handle.

    Provides methods for inspecting, purging, and directly
    accessing messages in the stream, as well as managing consumers.
    """

    @property
    def name(self) -> str:
        """Stream name."""

    @property
    def consumers(self) -> ConsumersManager:
        """Manager for consumers bound to this stream."""

    def direct_get(
        self,
        sequence: int,
        timeout: float | datetime | None = None,
    ) -> Future[StreamMessage]:
        """Get a message directly from the stream by sequence number.

        :param sequence: sequence number of the message to get.
        :param timeout: operation timeout.
        :return: the stream message.
        """

    def direct_get_next_for_subject(
        self,
        subject: str,
        sequence: int | None = None,
        timeout: float | timedelta | None = None,
    ) -> Future[StreamMessage]:
        """Get the next message for a subject directly from the stream.

        :param subject: subject to get the next message for.
        :param sequence: optional sequence number to start searching from.
            If not provided, starts from the beginning of the stream.
        :param timeout: operation timeout.
        :return: the next stream message matching the subject filter.
        """

    def direct_get_first_for_subject(
        self,
        subject: str,
        timeout: float | timedelta | None = None,
    ) -> Future[StreamMessage]:
        """Get the first message for a subject directly from the stream.

        :param subject: subject to get the first message for.
        :param timeout: operation timeout.
        :return: the first stream message matching the subject filter.
        """

    def direct_get_last_for_subject(
        self,
        subject: str,
        timeout: float | timedelta | None = None,
    ) -> Future[StreamMessage]:
        """Get the last message for a subject directly from the stream.

        :param subject: subject to get the last message for.
        :param timeout: operation timeout.
        :return: the last stream message matching the subject filter.
        """

    def get_info(self, timeout: float | datetime | None = None) -> Future[StreamInfo]:
        """Get information about the stream.

        :param timeout: operation timeout.
        :return: stream info.
        """

    def purge(
        self,
        filter: str | None = None,
        sequence: int | None = None,
        keep: int | None = None,
        timeout: float | datetime | None = None,
    ) -> Future[int]:
        """Purge messages from the stream.

        :param filter: subject filter for messages to purge,
            defaults to None.
        :param sequence: purge messages up to this sequence number
            inclusive, defaults to None.
        :param keep: number of messages to keep starting from the end
            of the stream, defaults to None.
        :param timeout: operation timeout.
        :return: number of messages purged.
        """

    def delete_message(
        self,
        sequence: int,
        timeout: float | datetime | None = None,
    ) -> Future[None]:
        """Delete a message from the stream by sequence number.

        :param sequence: sequence number of the message to delete.
        :param timeout: operation timeout.
        """
