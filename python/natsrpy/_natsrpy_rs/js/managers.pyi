from datetime import timedelta
from typing import final, overload

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
    "ConsumersManager",
    "CountersManager",
    "KVManager",
    "ObjectStoreManager",
    "StreamsManager",
]

@final
class StreamsManager:
    """Manager for JetStream stream CRUD operations."""

    async def create(self, config: StreamConfig) -> Stream:
        """Create a new stream.

        :param config: stream configuration.
        :return: the created stream.
        """

    async def create_or_update(self, config: StreamConfig) -> Stream:
        """Create a stream or update it if it already exists.

        :param config: stream configuration.
        :return: the created or updated stream.
        """

    async def get(self, name: str) -> Stream:
        """Get an existing stream by name.

        :param name: stream name.
        :return: the stream.
        """

    async def delete(self, name: str) -> bool:
        """Delete a stream.

        :param name: stream name.
        :return: True if the stream was deleted.
        """

    async def update(self, config: StreamConfig) -> Stream:
        """Update an existing stream configuration.

        :param config: new stream configuration.
        :return: the updated stream.
        """

@final
class CountersManager:
    """Manager for JetStream stream with counters support CRUD operations."""

    async def create(self, config: CountersConfig) -> Counters:
        """Create a new counters stream.

        :param config: stream configuration.
        :return: the created stream.
        """

    async def create_or_update(self, config: CountersConfig) -> Counters:
        """Create a counters stream or update it if it already exists.

        :param config: stream configuration.
        :return: the created or updated stream.
        """

    async def get(self, name: str) -> Counters:
        """Get an existing counters stream by name.

        :param name: stream name.
        :return: the stream.
        """

    async def delete(self, name: str) -> bool:
        """Delete a counters stream.

        :param name: stream name.
        :return: True if the stream was deleted.
        """

    async def update(self, config: StreamConfig) -> Counters:
        """Update an existing counters stream configuration.

        :param config: new stream configuration.
        :return: the updated stream.
        """

@final
class KVManager:
    """Manager for key-value bucket CRUD operations."""

    async def create(self, config: KVConfig) -> KeyValue:
        """Create a new key-value bucket.

        :param config: bucket configuration.
        :return: the created key-value bucket.
        """

    async def create_or_update(self, config: KVConfig) -> KeyValue:
        """Create a bucket or update it if it already exists.

        :param config: bucket configuration.
        :return: the created or updated key-value bucket.
        """

    async def get(self, bucket: str) -> KeyValue:
        """Get an existing key-value bucket by name.

        :param bucket: bucket name.
        :return: the key-value bucket.
        """

    async def delete(self, bucket: str) -> bool:
        """Delete a key-value bucket.

        :param bucket: bucket name.
        :return: True if the bucket was deleted.
        """

    async def update(self, config: KVConfig) -> KeyValue:
        """Update an existing key-value bucket configuration.

        :param config: new bucket configuration.
        :return: the updated key-value bucket.
        """

@final
class ConsumersManager:
    """Manager for JetStream consumer CRUD operations."""

    @overload
    async def create(self, config: PullConsumerConfig) -> PullConsumer: ...
    @overload
    async def create(self, config: PushConsumerConfig) -> PushConsumer: ...
    @overload
    async def update(self, config: PullConsumerConfig) -> PullConsumer: ...
    @overload
    async def update(self, config: PushConsumerConfig) -> PushConsumer: ...
    async def get_pull(self, name: str) -> PullConsumer:
        """Get an existing pull consumer by name.

        :param name: consumer name.
        :return: the pull consumer.
        """

    async def get_push(self, name: str) -> PushConsumer:
        """Get an existing push consumer by name.

        :param name: consumer name.
        :return: the push consumer.
        """

    async def delete(self, name: str) -> bool:
        """Delete a consumer.

        :param name: consumer name.
        :return: True if the consumer was deleted.
        """

    async def pause(self, name: str, delay: float | timedelta) -> bool:
        """Pause a consumer for a specified duration.

        :param name: consumer name.
        :param delay: duration to pause in seconds or as a timedelta.
        :return: True if the consumer was paused.
        """

    async def resume(self, name: str) -> bool:
        """Resume a paused consumer.

        :param name: consumer name.
        :return: True if the consumer was resumed.
        """

@final
class ObjectStoreManager:
    """Manager for object store bucket operations."""

    async def create(self, config: ObjectStoreConfig) -> ObjectStore:
        """Create a new object store bucket.

        :param config: object store configuration.
        :return: the created object store.
        """

    async def get(self, bucket: str) -> ObjectStore:
        """Get an existing object store bucket by name.

        :param bucket: bucket name.
        :return: the object store.
        """

    async def delete(self, bucket: str) -> None:
        """Delete an object store bucket.

        :param bucket: bucket name.
        """
