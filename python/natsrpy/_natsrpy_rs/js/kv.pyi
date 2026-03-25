from datetime import datetime, timedelta
from typing import final

from typing_extensions import Self

from .stream import (
    Placement,
    Republish,
    Source,
    StorageType,
    StreamInfo,
)

__all__ = [
    "KVConfig",
    "KVEntry",
    "KVEntryIterator",
    "KVOperation",
    "KVStatus",
    "KeyValue",
    "KeysIterator",
]

@final
class KVStatus:
    info: StreamInfo
    bucket: str

@final
class KVOperation:
    Put: KVOperation
    Delete: KVOperation
    Purge: KVOperation

@final
class KVEntry:
    @property
    def bucket(self) -> str: ...
    @property
    def key(self) -> str: ...
    @property
    def value(self) -> bytes: ...
    @property
    def revision(self) -> int: ...
    @property
    def delta(self) -> int: ...
    @property
    def created(self) -> datetime: ...
    @property
    def operation(self) -> KVOperation: ...
    @property
    def seen_current(self) -> bool: ...

@final
class KVEntryIterator:
    def __aiter__(self) -> Self: ...
    async def __anext__(self) -> KVEntry: ...
    async def next(self, timeout: float | timedelta | None = None) -> KVEntry: ...

@final
class KeysIterator:
    def __aiter__(self) -> Self: ...
    async def __anext__(self) -> str: ...
    async def next(self, timeout: float | timedelta | None = None) -> str: ...

@final
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

    def __new__(
        cls,
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
    ) -> Self: ...

@final
class KeyValue:
    @property
    def stream_name(self) -> str: ...
    @property
    def prefix(self) -> str: ...
    @property
    def put_prefix(self) -> str | None: ...
    @property
    def use_jetstream_prefix(self) -> bool: ...
    @property
    def name(self) -> str: ...
    async def get(self, key: str) -> bytes | None: ...
    async def delete(
        self,
        key: str,
        expect_revision: int | None = None,
    ) -> int: ...
    async def update(self, key: str, value: bytes | str, revision: int) -> None: ...
    async def create(
        self,
        key: str,
        value: bytes | str,
        ttl: float | timedelta | None = None,
    ) -> int: ...
    async def put(self, key: str, value: bytes | str) -> int: ...
    async def purge(
        self,
        key: str,
        ttl: float | timedelta | None = None,
        expect_revision: int | None = None,
    ) -> None: ...
    async def history(self, key: str) -> KVEntryIterator: ...
    async def entry(self, key: str, revision: int | None = None) -> KVEntry | None: ...
    async def watch(
        self,
        key: str,
        from_revision: int | None = None,
    ) -> KVEntryIterator: ...
    async def watch_with_history(self, key: str) -> KVEntryIterator: ...
    async def watch_all(self, from_revision: int | None = None) -> KVEntryIterator: ...
    async def watch_many(self, keys: list[str]) -> KVEntryIterator: ...
    async def watch_many_with_history(self, keys: list[str]) -> KVEntryIterator: ...
    async def keys(self) -> KeysIterator: ...
    async def status(self) -> KVStatus: ...
