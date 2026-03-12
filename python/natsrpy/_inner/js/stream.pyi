from datetime import timedelta

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
    def __init__(
        self,
        name: str,
        subjects,
        max_bytes=None,
        max_messages=None,
        max_messages_per_subject=None,
        discard=None,
        discard_new_per_subject=None,
        retention=None,
        max_consumers=None,
        max_age=None,
        max_message_size=None,
        storage=None,
        num_replicas=None,
        no_ack=None,
        duplicate_window=None,
        template_owner=None,
        sealed=None,
        description=None,
        allow_rollup=None,
        deny_delete=None,
        deny_purge=None,
        republish=None,
        allow_direct=None,
        mirror_direct=None,
        mirror=None,
        sources=None,
        metadata=None,
        subject_transform=None,
        compression=None,
        consumer_limits=None,
        first_sequence=None,
        placement=None,
        persist_mode=None,
        pause_until=None,
        allow_message_ttl=None,
        subject_delete_marker_ttl=None,
        allow_atomic_publish=None,
        allow_message_schedules=None,
        allow_message_counter=None,
    ) -> None: ...
