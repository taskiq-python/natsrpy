from typing import Any

from .managers import KVManager, StreamsManager

class JetStream:
    async def publish(
        self,
        subject: str,
        payload: str | bytes | bytearray | memoryview,
        *,
        headers: dict[str, str] | None = None,
        reply: str | None = None,
        err_on_disconnect: bool = False,
    ) -> None: ...
    @property
    def kv(self) -> KVManager: ...
    @property
    def streams(self) -> StreamsManager: ...

class JetStreamMessage:
    @property
    def subject(self) -> str: ...
    @property
    def reply(self) -> str | None: ...
    @property
    def payload(self) -> bytes: ...
    @property
    def headers(self) -> dict[str, Any]: ...
    async def ack(self) -> None: ...
