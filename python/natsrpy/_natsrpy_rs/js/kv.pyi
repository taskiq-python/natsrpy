from asyncio import Future
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
    """Status information for a key-value bucket.

    Attributes:
        info: underlying stream information.
        bucket: name of the key-value bucket.
    """

    info: StreamInfo
    bucket: str

@final
class KVOperation:
    """Type of operation recorded in a key-value entry.

    Attributes:
        Put: a value was written or updated.
        Delete: the key was deleted.
        Purge: the key history was purged.
    """

    Put: KVOperation
    Delete: KVOperation
    Purge: KVOperation

@final
class KVEntry:
    """A single key-value entry from a watch or history query."""

    @property
    def bucket(self) -> str:
        """Name of the key-value bucket."""

    @property
    def key(self) -> str:
        """Key of the entry."""

    @property
    def value(self) -> bytes:
        """Value payload."""

    @property
    def revision(self) -> int:
        """Revision number of the entry."""

    @property
    def delta(self) -> int:
        """Number of pending entries for the watcher."""

    @property
    def created(self) -> datetime:
        """Timestamp when this revision was created."""

    @property
    def operation(self) -> KVOperation:
        """Operation type that produced this entry."""

    @property
    def seen_current(self) -> bool:
        """Whether all historical entries have been delivered."""

@final
class KVEntryIterator:
    """Async iterator over key-value entries."""

    def __aiter__(self) -> Self: ...
    def __anext__(self) -> Future[KVEntry]: ...

@final
class KeysIterator:
    """Async iterator over key-value bucket keys."""

    def __aiter__(self) -> Self: ...
    def __anext__(self) -> Future[str]: ...

@final
class KVConfig:
    """Configuration for creating or updating a key-value bucket.

    Attributes:
        bucket: bucket name.
        description: human-readable bucket description.
        max_value_size: maximum size of a single value in bytes.
        history: number of historical revisions to keep per key.
        max_age: maximum entry age in seconds.
        max_bytes: maximum total bucket size in bytes.
        storage: storage backend type.
        num_replicas: number of bucket replicas.
        republish: configuration for republishing changes.
        mirror: source configuration when the bucket is a mirror.
        sources: list of source configurations for aggregate buckets.
        mirror_direct: when True, enable direct get for mirror buckets.
        compression: when True, enable S2 compression.
        placement: cluster and tag placement hints.
        limit_markers: TTL for delete markers in seconds, also enables
            per-message TTL support on the bucket when set.
    """

    bucket: str
    description: str | None
    max_value_size: int | None
    history: int | None
    max_age: timedelta | None
    max_bytes: int | None
    storage: StorageType | None
    num_replicas: int | None
    republish: Republish | None
    mirror: Source | None
    sources: list[Source] | None
    mirror_direct: bool | None
    compression: bool | None
    placement: Placement | None
    limit_markers: timedelta | None

    def __new__(
        cls,
        bucket: str,
        description: str | None = None,
        max_value_size: int | None = None,
        history: int | None = None,
        max_age: float | timedelta | None = None,
        max_bytes: int | None = None,
        storage: StorageType | None = None,
        num_replicas: int | None = None,
        republish: Republish | None = None,
        mirror: Source | None = None,
        sources: list[Source] | None = None,
        mirror_direct: bool | None = None,
        compression: bool | None = None,
        placement: Placement | None = None,
        limit_markers: float | timedelta | None = None,
    ) -> Self: ...

@final
class KeyValue:
    """Handle for a NATS JetStream key-value bucket.

    Provides CRUD operations, watching for changes, and iteration
    over keys and entries.
    """

    @property
    def stream_name(self) -> str:
        """Name of the underlying JetStream stream."""

    @property
    def prefix(self) -> str:
        """Subject prefix used for key-value operations."""

    @property
    def put_prefix(self) -> str | None:
        """Subject prefix used for put operations, if different."""

    @property
    def use_jetstream_prefix(self) -> bool:
        """Whether the JetStream API prefix is used."""

    @property
    def name(self) -> str:
        """Name of the key-value bucket."""

    def get(self, key: str) -> Future[bytes | None]:
        """Get the current value for a key.

        :param key: key to look up.
        :return: value bytes, or None if the key does not exist.
        """

    def delete(
        self,
        key: str,
        expect_revision: int | None = None,
    ) -> Future[int]:
        """Delete a key from the bucket.

        :param key: key to delete.
        :param expect_revision: expected current revision for optimistic
            concurrency control, defaults to None.
        :return: the new revision number.
        """

    def update(self, key: str, value: bytes | str, revision: int) -> Future[None]:
        """Update a key only if it matches the expected revision.

        :param key: key to update.
        :param value: new value.
        :param revision: expected current revision.
        """

    def create(
        self,
        key: str,
        value: bytes | str,
        ttl: float | timedelta | None = None,
    ) -> Future[int]:
        """Create a new key.

        Fails if the key already exists.

        :param key: key to create.
        :param value: value to store.
        :param ttl: optional time-to-live in seconds or as a timedelta.
        :return: the initial revision number.
        """

    def put(self, key: str, value: bytes | str) -> Future[int]:
        """Put a value for a key, creating or updating as needed.

        :param key: key to set.
        :param value: value to store.
        :return: the new revision number.
        """

    def purge(
        self,
        key: str,
        ttl: float | timedelta | None = None,
        expect_revision: int | None = None,
    ) -> Future[None]:
        """Purge all revisions of a key.

        :param key: key to purge.
        :param ttl: optional time-to-live for the purge marker in seconds
            or as a timedelta.
        :param expect_revision: expected current revision for optimistic
            concurrency control, defaults to None.
        """

    def history(self, key: str) -> Future[KVEntryIterator]:
        """Get the revision history for a key.

        :param key: key to query.
        :return: an async iterator over historical entries.
        """

    def entry(self, key: str, revision: int | None = None) -> Future[KVEntry | None]:
        """Get a specific entry for a key.

        :param key: key to look up.
        :param revision: specific revision to retrieve, defaults to the
            latest.
        :return: the entry, or None if not found.
        """

    def watch(
        self,
        key: str,
        from_revision: int | None = None,
    ) -> Future[KVEntryIterator]:
        """Watch a key for changes.

        :param key: key to watch.
        :param from_revision: start watching from this revision,
            defaults to the latest.
        :return: an async iterator over entry changes.
        """

    def watch_with_history(self, key: str) -> Future[KVEntryIterator]:
        """Watch a key for changes, delivering all historical entries first.

        :param key: key to watch.
        :return: an async iterator starting with history then live changes.
        """

    def watch_all(self, from_revision: int | None = None) -> Future[KVEntryIterator]:
        """Watch all keys in the bucket for changes.

        :param from_revision: start watching from this revision,
            defaults to the latest.
        :return: an async iterator over entry changes.
        """

    def watch_many(self, keys: list[str]) -> Future[KVEntryIterator]:
        """Watch multiple keys for changes.

        :param keys: list of keys to watch.
        :return: an async iterator over entry changes.
        """

    def watch_many_with_history(self, keys: list[str]) -> Future[KVEntryIterator]:
        """Watch multiple keys, delivering all historical entries first.

        :param keys: list of keys to watch.
        :return: an async iterator starting with history then live changes.
        """

    def keys(self) -> Future[KeysIterator]:
        """List all keys in the bucket.

        :return: an async iterator over key names.
        """

    def status(self) -> Future[KVStatus]:
        """Get the status of the key-value bucket.

        :return: bucket status information.
        """
