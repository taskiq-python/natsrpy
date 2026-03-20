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
