from datetime import datetime, timedelta
from typing import Any

class StorageType:
    FILE: "StorageType"
    MEMORY: "StorageType"

class DiscardPolicy:
    OLD: "DiscardPolicy"
    NEW: "DiscardPolicy"

class RetentionPolicy:
    LIMITS: "RetentionPolicy"
    INTEREST: "RetentionPolicy"
    WORKQUEUE: "RetentionPolicy"

class Compression:
    S2: "Compression"
    NONE: "Compression"

class PersistenceMode:
    Default: "PersistenceMode"
    Async: "PersistenceMode"

class ConsumerLimits:
    inactive_threshold: timedelta
    max_ack_pending: int

    def __init__(self, inactive_threshold: timedelta, max_ack_pending: int) -> None: ...

class External:
    api_prefix: str
    delivery_prefix: str | None

    def __init__(
        self,
        api_prefix: str,
        delivery_prefix: str | None = None,
    ) -> None: ...

class SubjectTransform:
    source: str
    destination: str

    def __init__(
        self,
        source: str,
        destination: str,
    ) -> None: ...

class Source:
    name: str
    filter_subject: str | None = None
    external: External | None = None
    start_sequence: int | None = None
    start_time: int | None = None
    domain: str | None = None
    subject_transforms: SubjectTransform | None = None

    def __init__(
        self,
        name: str,
        filter_subject: str | None = None,
        external: External | None = None,
        start_sequence: int | None = None,
        start_time: int | None = None,
        domain: str | None = None,
        subject_transforms: SubjectTransform | None = None,
    ) -> None: ...

class Placement:
    cluster: str | None
    tags: list[str] | None

    def __init__(
        self,
        cluster: str | None = None,
        tags: list[str] | None = None,
    ) -> None: ...

class Republish:
    source: str
    destination: str
    headers_only: bool

    def __init__(
        self,
        source: str,
        destination: str,
        headers_only: bool,
    ) -> None: ...

class StreamConfig:
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

    def __init__(
        self,
        name: str,
        subjects: list[str],
        max_bytes: int | None = None,
        max_messages: int | None = None,
        max_messages_per_subject: int | None = None,
        discard: DiscardPolicy | None = None,
        discard_new_per_subject: bool | None = None,
        retention: RetentionPolicy | None = None,
        max_consumers: int | None = None,
        max_age: timedelta | None = None,
        max_message_size: int | None = None,
        storage: StorageType | None = None,
        num_replicas: int | None = None,
        no_ack: bool | None = None,
        duplicate_window: timedelta | None = None,
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
        subject_delete_marker_ttl: timedelta | None = None,
        allow_atomic_publish: bool | None = None,
        allow_message_schedules: bool | None = None,
        allow_message_counter: bool | None = None,
    ) -> None: ...

class StreamMessage:
    subject: str
    sequence: int
    headers: dict[str, Any]
    payload: bytes
    time: datetime

class Stream:
    async def direct_get(self, sequence: int) -> StreamMessage:
        """
        Get direct message from a stream.

        Please note, that this method will throw an error
        in case of stream being configured without `allow_direct=True`.
        """
