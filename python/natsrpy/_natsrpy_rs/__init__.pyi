from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any

from natsrpy._natsrpy_rs.js import JetStream
from natsrpy._natsrpy_rs.message import Message

class Subscription:
    def __aiter__(self) -> Subscription: ...
    async def __anext__(self) -> Message: ...
    async def unsubscribe(self, limit: int | None = None) -> None: ...
    async def drain(self) -> None: ...

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
        connection_timeout: float | timedelta = ...,
        request_timeout: float | timedelta = ...,
    ) -> None: ...
    async def startup(self) -> None: ...
    async def shutdown(self) -> None: ...
    async def publish(
        self,
        subject: str,
        payload: bytes | str | bytearray | memoryview,
        *,
        headers: dict[str, Any] | None = None,
        reply: str | None = None,
        err_on_disconnect: bool = False,
    ) -> None: ...
    async def request(self, subject: str, payload: bytes) -> None: ...
    async def drain(self) -> None: ...
    async def flush(self) -> None: ...
    async def subscribe(
        self,
        subject: str,
        callback: Callable[[Message], Awaitable[None]] | None = None,
    ) -> Subscription: ...
    async def jetstream(self) -> JetStream: ...

__all__ = ["Message", "Nats", "Subscription"]
