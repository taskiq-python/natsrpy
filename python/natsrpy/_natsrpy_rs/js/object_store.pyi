from datetime import timedelta

from typing_extensions import Writer

from .stream import Placement, StorageType

class ObjectStoreConfig:
    bucket: str
    description: str | None
    max_age: timedelta
    max_bytes: int
    storage: StorageType
    num_replicas: int
    compression: bool
    placement: Placement | None

    def __init__(
        self,
        bucket: str,
        description: str | None = None,
        max_age: float | timedelta | None = None,
        max_bytes: int | None = None,
        storage: StorageType | None = None,
        num_replicas: int | None = None,
        compression: bool | None = None,
        placement: Placement | None = None,
    ) -> None: ...

class ObjectStore:
    async def get(
        self,
        name: str,
        writer: Writer[bytes],
        buf_size: int | None = None,
    ) -> None: ...
    async def put(
        self,
        name: str,
        value: bytes | str,
        chunk_size: int = 24576,  # 24MB
        description: str | None = None,
        headers: dict[str, str | list[str]] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None: ...
    async def delete(self, name: str) -> None: ...
