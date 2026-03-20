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
