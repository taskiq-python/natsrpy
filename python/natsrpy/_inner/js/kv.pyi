from natsrpy._inner.js.stream import StorageType, Source, Placement, Republish

class KVConfig:
    """
    KV bucket config.

    Used for creating or updating KV buckets.
    """

    bucket: str
    description: str
    max_value_size: int | None
    history: int | None
    max_age: float | None
    max_bytes: int | None
    storage: StorageType | None
    num_replicas: int | None
    republish: Republish | None
    mirror: Source | None
    sources: list[Source] | None
    mirror_direct: bool | None
    compression: bool | None
    placement: Placement | None
    limit_markers: float | None

    def __init__(
        self,
        bucket: str,
        description: str | None = None,
        max_value_size: int | None = None,
        history: int | None = None,
        max_age: float | None = None,
        max_bytes: int | None = None,
        storage: StorageType | None = None,
        num_replicas: int | None = None,
        republish: Republish | None = None,
        mirror: Source | None = None,
        sources: list[Source] | None = None,
        mirror_direct: bool | None = None,
        compression: bool | None = None,
        placement: Placement | None = None,
        limit_markers: float | None = None,
    ) -> None: ...

class KeyValue:
    async def put(self, key: str, value: bytes) -> int: ...
    async def get(self, key: str) -> bytes | None: ...
    async def delete(self, key: str) -> int: ...
