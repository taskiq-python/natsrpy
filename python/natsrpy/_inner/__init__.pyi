from natsrpy._inner.js import JetStream
from natsrpy._inner.message import Message

class Subscription:
    def __aiter__(self) -> "Subscription": ...
    async def __anext__(self) -> Message: ...

class Nats:
    def __init__(
        self,
        /,
        addrs: list[str] = ["nats://localhost:4222"],
        user_and_pass=None,
        nkey=None,
        token=None,
        custom_inbox_prefix=None,
        read_buffer_capacity=65535,
        sender_capacity=128,
        max_reconnects=None,
        connection_timeout=5.0,
        request_timeout=10.0,
    ) -> None: ...
    async def startup(self) -> None: ...
    async def publish(
        self,
        subject: str,
        payload: bytes,
        *,
        headers: dict[str, str] | None = None,
        reply: str | None = None,
        err_on_disconnect: bool = False,
    ) -> None: ...
    async def request(self, subject: str, payload: bytes) -> None: ...
    async def drain(self) -> None: ...
    async def flush(self) -> None: ...
    async def close(self) -> None: ...
    async def subscribe(self, topic: str) -> Subscription: ...
    async def jetstream(self) -> JetStream: ...

__all__ = ["Subscription", "Nats", "Message"]
