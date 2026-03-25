from datetime import datetime, timedelta
from typing import Any, final

from typing_extensions import Self, Writer

from .stream import Placement, StorageType

__all__ = [
    "ObjectInfo",
    "ObjectInfoIterator",
    "ObjectLink",
    "ObjectStore",
    "ObjectStoreConfig",
]

@final
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

@final
class ObjectLink:
    name: str | None
    bucket: str

@final
class ObjectInfo:
    name: str
    description: str | None
    metadata: dict[str, str]
    headers: dict[str, Any]
    bucket: str
    nuid: str
    size: int
    chunks: int
    modified: datetime | None
    digest: str | None
    deleted: bool
    link: ObjectLink | None
    max_chunk_size: int | None

@final
class ObjectInfoIterator:
    def __aiter__(self) -> Self: ...
    async def __anext__(self) -> ObjectInfo: ...
    async def next(self, timeout: float | timedelta | None = None) -> ObjectInfo: ...

@final
class ObjectStore:
    async def get(
        self,
        name: str,
        writer: Writer[bytes],
        chunk_size: int | None = ...,  # 24MB
    ) -> None: ...
    async def put(
        self,
        name: str,
        value: bytes | str,
        chunk_size: int = ...,  # 24MB
        description: str | None = None,
        headers: dict[str, str | list[str]] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None: ...
    async def delete(self, name: str) -> None: ...
    async def seal(self) -> None: ...
    async def get_info(self, name: str) -> ObjectInfo: ...
    async def watch(self, with_history: bool = False) -> ObjectInfoIterator: ...
    async def list(self) -> ObjectInfoIterator: ...
    async def link_bucket(self, src_bucket: str, dest: str) -> ObjectInfo: ...
    async def link_object(self, src: str, dest: str) -> ObjectInfo: ...
    async def update_metadata(
        self,
        name: str,
        new_name: str | None = None,
        description: str | None = None,
        headers: dict[str, Any] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> ObjectInfo: ...
