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
    ALL: DeliverPolicy
    LAST: DeliverPolicy
    NEW: DeliverPolicy
    BY_START_SEQUENCE: DeliverPolicy
    BY_START_TIME: DeliverPolicy
    LAST_PER_SUBJECT: DeliverPolicy

@final
class AckPolicy:
    EXPLICIT: AckPolicy
    NONE: AckPolicy
    ALL: AckPolicy

@final
class ReplayPolicy:
    INSTANT: ReplayPolicy
    ORIGINAL: ReplayPolicy

@final
class PriorityPolicy:
    NONE: PriorityPolicy
    OVERFLOW: PriorityPolicy
    PINNED_CLIENT: PriorityPolicy
    PRIORITIZED: PriorityPolicy

@final
class PullConsumerConfig:
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
    def __aiter__(self) -> Self: ...
    async def __anext__(self) -> JetStreamMessage: ...
    async def next(
        self,
        timeout: float | timedelta | None = None,
    ) -> JetStreamMessage: ...

@final
class PushConsumer:
    async def messages(self) -> MessagesIterator: ...

@final
class PullConsumer:
    async def fetch(
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
    ) -> list[JetStreamMessage]: ...
