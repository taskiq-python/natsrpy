from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any, final, overload

from typing_extensions import Self

from . import js

@final
class Message:
    """
    Simple NATS message.

    Attributes:
        subject: subject where message was published
        reply: subject where reply should be sent, if any
        payload: message payload
        headers: dictionary of message headers,
            every value can be a simple value or a list.
        status: status is used for reply messages to indicate the status of the reply.
            It is None for regular messages.
        description: message description is used for reply messages to
            provide additional information about the status.
        length: a length of the message payload in bytes.
    """

    subject: str
    reply: str | None
    payload: bytes
    headers: dict[str, Any]
    status: int | None
    description: str | None
    length: int

@final
class IteratorSubscription:
    def __aiter__(self) -> IteratorSubscription: ...
    async def __anext__(self) -> Message: ...
    async def next(self, timeout: float | timedelta | None = None) -> Message: ...
    async def unsubscribe(self, limit: int | None = None) -> None: ...
    async def drain(self) -> None: ...

@final
class CallbackSubscription:
    async def unsubscribe(self, limit: int | None = None) -> None: ...
    async def drain(self) -> None: ...

@final
class Nats:
    def __new__(
        cls,
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
    ) -> Self: ...
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
    async def request(
        self,
        subject: str,
        payload: bytes | str | bytearray | memoryview,
        *,
        headers: dict[str, Any] | None = None,
        reply: str | None = None,
        err_on_disconnect: bool = False,
    ) -> None: ...
    async def drain(self) -> None: ...
    async def flush(self) -> None: ...
    @overload
    async def subscribe(
        self,
        subject: str,
        callback: Callable[[Message], Awaitable[None]],
    ) -> CallbackSubscription: ...
    @overload
    async def subscribe(
        self,
        subject: str,
        callback: None = None,
    ) -> IteratorSubscription: ...
    async def jetstream(self) -> js.JetStream: ...

__all__ = ["CallbackSubscription", "IteratorSubscription", "Message", "Nats", "js"]
