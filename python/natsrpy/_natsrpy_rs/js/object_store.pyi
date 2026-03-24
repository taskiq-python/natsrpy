from datetime import timedelta

from typing_extensions import Self, Writer

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

    def __new__(
        cls,
        bucket: str,
        description: str | None = None,
        max_age: float | timedelta | None = None,
        max_bytes: int | None = None,
        storage: StorageType | None = None,
        num_replicas: int | None = None,
        compression: bool | None = None,
        placement: Placement | None = None,
    ) -> Self: ...

class ObjectStore:
    async def get(
        self,
        name: str,
        writer: Writer[bytes],
        chunk_size: int | None = 24576,  # 24MB
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
