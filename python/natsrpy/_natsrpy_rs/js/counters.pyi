from datetime import timedelta
from typing import final

from typing_extensions import Self

from .stream import (
    Compression,
    ConsumerLimits,
    DiscardPolicy,
    PersistenceMode,
    Placement,
    Republish,
    RetentionPolicy,
    Source,
    StorageType,
    SubjectTransform,
)

__all__ = ["Counters", "CountersConfig"]

@final
class CountersConfig:
    """Configuration for creating or updating a JetStream stream.

    This config is almost the same as `StreamConfig`,
    but it has 2 predefined values;

    * allow_message_counter=true
    * allow_direct=true

    These two are required for counters API to work.

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
    ) -> Self: ...

@final
class Counters:
    async def add(
        self,
        key: str,
        value: int,
        timeout: float | timedelta | None = None,
    ) -> int: ...
    async def incr(
        self,
        key: str,
        timeout: float | timedelta | None = None,
    ) -> int: ...
    async def decr(
        self,
        key: str,
        timeout: float | timedelta | None = None,
    ) -> int: ...
