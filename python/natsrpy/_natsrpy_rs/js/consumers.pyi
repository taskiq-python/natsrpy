from datetime import timedelta

class DeliverPolicy:
    ALL: DeliverPolicy
    LAST: DeliverPolicy
    NEW: DeliverPolicy
    BY_START_SEQUENCE: DeliverPolicy
    BY_START_TIME: DeliverPolicy
    LAST_PER_SUBJECT: DeliverPolicy

class AckPolicy:
    EXPLICIT: AckPolicy
    NONE: AckPolicy
    ALL: AckPolicy

class ReplayPolicy:
    INSTANT: ReplayPolicy
    ORIGINAL: ReplayPolicy

class PriorityPolicy:
    NONE: PriorityPolicy
    OVERFLOW: PriorityPolicy
    PINNED_CLIENT: PriorityPolicy
    PRIORITIZED: PriorityPolicy

class PullConsumerConfig:
    durable_name: str | None
    name: str | None
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

    def __init__(
        self,
        durable_name: str | None = None,
        name: str | None = None,
        description: str | None = None,
        deliver_policy: DeliverPolicy | None = None,
        delivery_start_sequence: int | None = None,
        delivery_start_time: int | None = None,
        ack_policy: AckPolicy | None = None,
        ack_wait: timedelta | None = None,
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
        max_expires: timedelta | None = None,
        inactive_threshold: timedelta | None = None,
        num_replicas: int | None = None,
        memory_storage: bool | None = None,
        metadata: dict[str, str] | None = None,
        backoff: list[timedelta] | None = None,
        priority_policy: PriorityPolicy | None = None,
        priority_groups: list[str] | None = None,
        pause_until: int | None = None,
    ) -> None: ...

class PushConsumerConfig:
    deliver_subject: str
    durable_name: str | None
    name: str | None
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

    def __init__(
        self,
        deliver_subject: str,
        durable_name: str | None = None,
        name: str | None = None,
        description: str | None = None,
        deliver_group: str | None = None,
        deliver_policy: DeliverPolicy | None = None,
        delivery_start_sequence: int | None = None,
        delivery_start_time: int | None = None,
        ack_policy: AckPolicy | None = None,
        ack_wait: timedelta | None = None,
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
        idle_heartbeat: timedelta | None = None,
        num_replicas: int | None = None,
        memory_storage: bool | None = None,
        metadata: dict[str, str] | None = None,
        backoff: list[timedelta] | None = None,
        inactive_threshold: timedelta | None = None,
        pause_until: int | None = None,
    ) -> None: ...

class PushConsumer: ...
class PullConsumer: ...
