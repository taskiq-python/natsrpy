from asyncio import Future
from datetime import timedelta
from typing import final, overload

from typing_extensions import Self

from .consumers import (
    PullConsumer,
    PullConsumerConfig,
    PushConsumer,
    PushConsumerConfig,
)
from .counters import Counters, CountersConfig
from .kv import KeyValue, KVConfig
from .object_store import ObjectStore, ObjectStoreConfig
from .stream import Stream, StreamConfig

__all__ = [
    "ConsumersIterator",
    "ConsumersManager",
    "ConsumersNamesIterator",
    "CountersManager",
    "KVManager",
    "ObjectStoreManager",
    "StreamsManager",
]

@final
class ConsumersIterator:
    """Async iterator over consumers subscribed to a stream.

    Returned by :meth:`ConsumersManager.list`.
    Consumers can be received using ``async for`` or by calling :meth:`next`
    directly.

    Consumer type is identified by its config. If it has deliver_subject set,
    then PushConsumer is returned.
    """

    def __aiter__(self) -> Self: ...
    def __anext__(self) -> Future[PullConsumer | PushConsumer]: ...

@final
class ConsumersNamesIterator:
    """Async iterator over names of consumers subscribed to a stream.

    Returned by :meth:`ConsumersManager.list_names`.
    Consumer names can be received using ``async for`` or by calling :meth:`next`
    directly.
    """

    def __aiter__(self) -> Self: ...
    def __anext__(self) -> Future[str]: ...

@final
class StreamsManager:
    """Manager for JetStream stream CRUD operations."""

    def create(self, config: StreamConfig) -> Future[Stream]:
        """Create a new stream.

        :param config: stream configuration.
        :return: the created stream.
        """

    def create_or_update(self, config: StreamConfig) -> Future[Stream]:
        """Create a stream or update it if it already exists.

        :param config: stream configuration.
        :return: the created or updated stream.
        """

    def get(self, name: str) -> Future[Stream]:
        """Get an existing stream by name.

        :param name: stream name.
        :return: the stream.
        """

    def delete(self, name: str) -> Future[bool]:
        """Delete a stream.

        :param name: stream name.
        :return: True if the stream was deleted.
        """

    def update(self, config: StreamConfig) -> Future[Stream]:
        """Update an existing stream configuration.

        :param config: new stream configuration.
        :return: the updated stream.
        """

@final
class CountersManager:
    """Manager for JetStream stream with counters support CRUD operations."""

    def create(self, config: CountersConfig) -> Future[Counters]:
        """Create a new counters stream.

        :param config: stream configuration.
        :return: the created stream.
        """

    def create_or_update(self, config: CountersConfig) -> Future[Counters]:
        """Create a counters stream or update it if it already exists.

        :param config: stream configuration.
        :return: the created or updated stream.
        """

    def get(self, name: str) -> Future[Counters]:
        """Get an existing counters stream by name.

        :param name: stream name.
        :return: the stream.
        """

    def delete(self, name: str) -> Future[bool]:
        """Delete a counters stream.

        :param name: stream name.
        :return: True if the stream was deleted.
        """

    def update(self, config: CountersConfig) -> Future[Counters]:
        """Update an existing counters stream configuration.

        :param config: new stream configuration.
        :return: the updated stream.
        """

@final
class KVManager:
    """Manager for key-value bucket CRUD operations."""

    def create(self, config: KVConfig) -> Future[KeyValue]:
        """Create a new key-value bucket.

        :param config: bucket configuration.
        :return: the created key-value bucket.
        """

    def create_or_update(self, config: KVConfig) -> Future[KeyValue]:
        """Create a bucket or update it if it already exists.

        :param config: bucket configuration.
        :return: the created or updated key-value bucket.
        """

    def get(self, bucket: str) -> Future[KeyValue]:
        """Get an existing key-value bucket by name.

        :param bucket: bucket name.
        :return: the key-value bucket.
        """

    def delete(self, bucket: str) -> Future[bool]:
        """Delete a key-value bucket.

        :param bucket: bucket name.
        :return: True if the bucket was deleted.
        """

    def update(self, config: KVConfig) -> Future[KeyValue]:
        """Update an existing key-value bucket configuration.

        :param config: new bucket configuration.
        :return: the updated key-value bucket.
        """

@final
class ConsumersManager:
    """Manager for JetStream consumer CRUD operations."""

    @overload
    def create(self, config: PullConsumerConfig) -> Future[PullConsumer]: ...
    @overload
    def create(self, config: PushConsumerConfig) -> Future[PushConsumer]: ...
    @overload
    def update(self, config: PullConsumerConfig) -> Future[PullConsumer]: ...
    @overload
    def update(self, config: PushConsumerConfig) -> Future[PushConsumer]: ...
    def get_pull(self, name: str) -> Future[PullConsumer]:
        """Get an existing pull consumer by name.

        :param name: consumer name.
        :return: the pull consumer.
        """

    def get_push(self, name: str) -> Future[PushConsumer]:
        """Get an existing push consumer by name.

        :param name: consumer name.
        :return: the push consumer.
        """

    def delete(self, name: str) -> Future[bool]:
        """Delete a consumer.

        :param name: consumer name.
        :return: True if the consumer was deleted.
        """

    def pause(self, name: str, delay: float | timedelta) -> Future[bool]:
        """Pause a consumer for a specified duration.

        :param name: consumer name.
        :param delay: duration to pause in seconds or as a timedelta.
        :return: True if the consumer was paused.
        """

    def resume(self, name: str) -> Future[bool]:
        """Resume a paused consumer.

        :param name: consumer name.
        :return: True if the consumer was resumed.
        """

    def list(self) -> Future[ConsumersIterator]:
        """List consumers subscribed to the stream.

        This method iterates over all consumers on a
        stream and retunrns correct types, by looking
        at their config.

        If you only need names, use :meth:`ConsumersManager.list_names` instead.

        :return: an async iterator over consumers.
        """

    def list_names(self) -> Future[ConsumersNamesIterator]:
        """List names of consumers subscribed to the stream.

        This method iterates over all consumer names on a
        stream.

        :return: an async iterator over consumer names.
        """

@final
class ObjectStoreManager:
    """Manager for object store bucket operations."""

    def create(self, config: ObjectStoreConfig) -> Future[ObjectStore]:
        """Create a new object store bucket.

        :param config: object store configuration.
        :return: the created object store.
        """

    def get(self, bucket: str) -> Future[ObjectStore]:
        """Get an existing object store bucket by name.

        :param bucket: bucket name.
        :return: the object store.
        """

    def delete(self, bucket: str) -> Future[None]:
        """Delete an object store bucket.

        :param bucket: bucket name.
        """
