from asyncio import Future
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
    """Configuration for creating an object store bucket.

    Attributes:
        bucket: bucket name.
        description: human-readable bucket description.
        max_age: maximum object age.
        max_bytes: maximum total bucket size in bytes.
        storage: storage backend type.
        num_replicas: number of bucket replicas.
        compression: whether S2 compression is enabled.
        placement: cluster and tag placement hints.
    """

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
    """Reference link to another object or bucket.

    Attributes:
        name: name of the linked object, or None for a bucket link.
        bucket: name of the linked bucket.
    """

    name: str | None
    bucket: str

@final
class ObjectInfo:
    """Metadata for an object stored in the object store.

    Attributes:
        name: object name.
        description: human-readable object description.
        metadata: custom key-value metadata.
        headers: NATS message headers.
        bucket: name of the containing bucket.
        nuid: unique identifier for the object.
        size: total object size in bytes.
        chunks: number of chunks the object is split into.
        modified: last modification timestamp.
        digest: SHA-256 digest of the object content.
        deleted: whether the object is deleted.
        link: link reference if this is a linked object.
        max_chunk_size: maximum chunk size in bytes, if set.
    """

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
    """Async iterator over object info entries."""

    def __aiter__(self) -> Self: ...
    def __anext__(self) -> Future[ObjectInfo]: ...
    def next(self, timeout: float | timedelta | None = None) -> Future[ObjectInfo]:
        """Receive the next object info entry.

        :param timeout: maximum time to wait in seconds or as a timedelta,
            defaults to None (wait indefinitely).
        :return: the next object info.
        """

@final
class ObjectStore:
    """Handle for a NATS JetStream object store bucket.

    Provides methods for storing, retrieving, and managing large
    objects that are chunked across NATS messages.
    """

    def get(
        self,
        name: str,
        writer: Writer[bytes],
        chunk_size: int | None = ...,  # 24MB
    ) -> Future[None]:
        """Download an object from the store.

        Writes the object content to the given writer in chunks.

        :param name: name of the object to retrieve.
        :param writer: writable buffer that receives the object bytes.
        :param chunk_size: size of read chunks in bytes,
            defaults to 24 MB.
        """

    def put(
        self,
        name: str,
        value: bytes | str,
        chunk_size: int = ...,  # 24MB
        description: str | None = None,
        headers: dict[str, str | list[str]] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Future[None]:
        """Upload an object to the store.

        :param name: name for the stored object.
        :param value: object content.
        :param chunk_size: size of upload chunks in bytes,
            defaults to 24 MB.
        :param description: human-readable object description.
        :param headers: optional NATS headers.
        :param metadata: optional custom key-value metadata.
        """

    def delete(self, name: str) -> Future[None]:
        """Delete an object from the store.

        :param name: name of the object to delete.
        """

    def seal(self) -> Future[None]:
        """Seal the object store, making it read-only."""

    def get_info(self, name: str) -> Future[ObjectInfo]:
        """Get metadata for an object.

        :param name: name of the object.
        :return: object metadata.
        """

    def watch(self, with_history: bool = False) -> Future[ObjectInfoIterator]:
        """Watch the object store for changes.

        :param with_history: when True, deliver all existing entries
            before live updates, defaults to False.
        :return: an async iterator over object info changes.
        """

    def list(self) -> Future[ObjectInfoIterator]:
        """List all objects in the store.

        :return: an async iterator over object info entries.
        """

    def link_bucket(self, src_bucket: str, dest: str) -> Future[ObjectInfo]:
        """Create a link to another object store bucket.

        :param src_bucket: name of the source bucket to link.
        :param dest: name for the link in this store.
        :return: object info for the created link.
        """

    def link_object(self, src: str, dest: str) -> Future[ObjectInfo]:
        """Create a link to another object in the store.

        :param src: name of the source object to link.
        :param dest: name for the link in this store.
        :return: object info for the created link.
        """

    def update_metadata(
        self,
        name: str,
        new_name: str | None = None,
        description: str | None = None,
        headers: dict[str, Any] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Future[ObjectInfo]:
        """Update the metadata of an existing object.

        :param name: current name of the object.
        :param new_name: optional new name for the object.
        :param description: new description, if provided.
        :param headers: new headers, if provided.
        :param metadata: new custom metadata, if provided.
        :return: updated object info.
        """
