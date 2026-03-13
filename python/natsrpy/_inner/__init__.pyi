from datetime import timedelta
from typing import Any

from natsrpy._inner.js import JetStream
from natsrpy._inner.message import Message

class Subscription:
    def __aiter__(self) -> Subscription: ...
    async def __anext__(self) -> Message: ...

class Nats:
    def __init__(
        self,
        /,
        addrs: list[str] = ["nats://localhost:4222"],
        user_and_pass: tuple[str, str] | None = None,
        nkey: str | None = None,
        token: str | None = None,
        custom_inbox_prefix: str | None = None,
        read_buffer_capacity: int = 65535,
        sender_capacity: int = 128,
        max_reconnects: int | None = None,
        connection_timeout: timedelta = ...,
        request_timeout: timedelta = ...,
    ) -> None: ...
    async def startup(self) -> None: ...
    async def shutdown(self) -> None: ...
    async def publish(
        self,
        subject: str,
        payload: bytes,
        *,
        headers: dict[str, Any] | None = None,
        reply: str | None = None,
        err_on_disconnect: bool = False,
    ) -> None: ...
    async def request(self, subject: str, payload: bytes) -> None: ...
    async def drain(self) -> None: ...
    async def flush(self) -> None: ...
    async def subscribe(self, subject: str) -> Subscription: ...
    async def jetstream(self) -> JetStream: ...

__all__ = ["Message", "Nats", "Subscription"]
