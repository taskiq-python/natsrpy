class NatsrpyBaseError(Exception):
    """Base exception for all natsrpy errors."""

class NatsrpySessionError(NatsrpyBaseError):
    """Raised on connection or session-level errors."""

class NatsrpyPublishError(NatsrpyBaseError):
    """Raised when a publish operation fails."""

__all__ = [
    "NatsrpyBaseError",
    "NatsrpyPublishError",
    "NatsrpySessionError",
]
