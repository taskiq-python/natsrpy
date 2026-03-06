from .kv import KeyValue

class JetStream:
    async def publish(
        self,
        subject: str,
        payload: bytes,
        *,
        headers: dict[str, str] | None = None,
        reply: str | None = None,
        err_on_disconnect: bool = False,
    ) -> None: ...
    async def create_kv(self, bucket: str) -> KeyValue: ...
    async def get_kv(self, bucket: str) -> KeyValue: ...
