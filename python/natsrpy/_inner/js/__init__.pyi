from .kv import KeyValue

class External:
    def __init__(
        self,
        api_prefix: str,
        delivery_prefix: str | None = None,
    ) -> None: ...

class Source:
    def __init__(
        self,
        name: str,
        filter_subject: str | None = None,
        external: External | None = None,
    ) -> None: ...

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
    async def create_kv(
        self,
        bucket: str,
        description=None,
        max_value_size=None,
        history=None,
        max_age=None,
        max_bytes=None,
        storage=None,
        num_replicas=None,
        republish=None,
        mirror: Source | None = None,
        mirror_direct=None,
        compression=None,
        limit_markers=None,
    ) -> KeyValue: ...
    async def get_kv(self, bucket: str) -> KeyValue: ...
