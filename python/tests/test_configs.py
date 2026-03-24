from natsrpy.js import (
    AckPolicy,
    Compression,
    DeliverPolicy,
    DiscardPolicy,
    KVConfig,
    ObjectStoreConfig,
    PersistenceMode,
    PullConsumerConfig,
    PushConsumerConfig,
    ReplayPolicy,
    Republish,
    RetentionPolicy,
    StorageType,
    StreamConfig,
)


async def test_storage_type_values() -> None:
    assert StorageType.FILE is not None
    assert StorageType.MEMORY is not None
    assert StorageType.FILE != StorageType.MEMORY


async def test_discard_policy_values() -> None:
    assert DiscardPolicy.OLD is not None
    assert DiscardPolicy.NEW is not None
    assert DiscardPolicy.OLD != DiscardPolicy.NEW


async def test_retention_policy_values() -> None:
    assert RetentionPolicy.LIMITS is not None
    assert RetentionPolicy.INTEREST is not None
    assert RetentionPolicy.WORKQUEUE is not None


async def test_compression_values() -> None:
    assert Compression.S2 is not None
    assert Compression.NONE is not None
    assert Compression.S2 != Compression.NONE


async def test_persistence_mode_values() -> None:
    assert PersistenceMode.Default is not None
    assert PersistenceMode.Async is not None


async def test_deliver_policy_values() -> None:
    assert DeliverPolicy.ALL is not None
    assert DeliverPolicy.LAST is not None
    assert DeliverPolicy.NEW is not None
    assert DeliverPolicy.BY_START_SEQUENCE is not None
    assert DeliverPolicy.BY_START_TIME is not None
    assert DeliverPolicy.LAST_PER_SUBJECT is not None


async def test_ack_policy_values() -> None:
    assert AckPolicy.EXPLICIT is not None
    assert AckPolicy.NONE is not None
    assert AckPolicy.ALL is not None


async def test_replay_policy_values() -> None:
    assert ReplayPolicy.INSTANT is not None
    assert ReplayPolicy.ORIGINAL is not None


async def test_stream_config_defaults() -> None:
    config = StreamConfig(name="test", subjects=["test.>"])
    assert config.name == "test"
    assert config.subjects == ["test.>"]


async def test_stream_config_setters() -> None:
    config = StreamConfig(name="test", subjects=["test.>"])
    config.name = "new-name"
    assert config.name == "new-name"
    config.subjects = ["new.>"]
    assert config.subjects == ["new.>"]
    config.description = "a description"
    assert config.description == "a description"


async def test_stream_config_all_options() -> None:
    config = StreamConfig(
        name="full-test",
        subjects=["full.>"],
        max_bytes=1024,
        max_messages=100,
        max_messages_per_subject=10,
        discard=DiscardPolicy.NEW,
        retention=RetentionPolicy.WORKQUEUE,
        max_consumers=5,
        storage=StorageType.MEMORY,
        num_replicas=1,
        no_ack=False,
        description="full config",
        allow_rollup=False,
        deny_delete=False,
        deny_purge=False,
        allow_direct=True,
    )
    assert config.name == "full-test"
    assert config.subjects == ["full.>"]
    assert config.max_bytes == 1024
    assert config.max_messages == 100
    assert config.max_messages_per_subject == 10
    assert config.discard == DiscardPolicy.NEW
    assert config.retention == RetentionPolicy.WORKQUEUE
    assert config.max_consumers == 5
    assert config.storage == StorageType.MEMORY
    assert config.num_replicas == 1
    assert config.description == "full config"
    assert config.allow_direct is True


async def test_pull_consumer_config_defaults() -> None:
    config = PullConsumerConfig()
    assert config.name is None
    assert config.durable_name is None
    assert config.description is None


async def test_pull_consumer_config_setters() -> None:
    config = PullConsumerConfig(name="test-consumer")
    config.name = "updated-name"
    assert config.name == "updated-name"
    config.description = "updated description"
    assert config.description == "updated description"


async def test_pull_consumer_config_policies() -> None:
    config = PullConsumerConfig(
        ack_policy=AckPolicy.ALL,
        deliver_policy=DeliverPolicy.LAST,
        replay_policy=ReplayPolicy.ORIGINAL,
    )
    assert config.ack_policy == AckPolicy.ALL
    assert config.deliver_policy == DeliverPolicy.LAST
    assert config.replay_policy == ReplayPolicy.ORIGINAL


async def test_push_consumer_config_defaults() -> None:
    config = PushConsumerConfig(deliver_subject="test.subject")
    assert config.deliver_subject == "test.subject"
    assert config.name is None


async def test_push_consumer_config_setters() -> None:
    config = PushConsumerConfig(deliver_subject="test.subject")
    config.deliver_subject = "new.subject"
    assert config.deliver_subject == "new.subject"
    config.name = "push-consumer"
    assert config.name == "push-consumer"


async def test_kv_config_defaults() -> None:
    config = KVConfig(bucket="test-bucket")
    assert config.bucket == "test-bucket"
    assert config.description is None


async def test_kv_config_setters() -> None:
    config = KVConfig(bucket="test-bucket")
    config.bucket = "new-bucket"
    assert config.bucket == "new-bucket"
    config.description = "test desc"
    assert config.description == "test desc"
    config.history = 5
    assert config.history == 5


async def test_kv_config_all_options() -> None:
    config = KVConfig(
        bucket="full-kv",
        description="full kv config",
        history=10,
        storage=StorageType.MEMORY,
        num_replicas=1,
    )
    assert config.bucket == "full-kv"
    assert config.description == "full kv config"
    assert config.history == 10
    assert config.storage == StorageType.MEMORY
    assert config.num_replicas == 1


async def test_object_store_config_defaults() -> None:
    config = ObjectStoreConfig(bucket="test-bucket")
    assert config.bucket == "test-bucket"
    assert config.description is None


async def test_object_store_config_setters() -> None:
    config = ObjectStoreConfig(bucket="test-bucket")
    config.bucket = "new-bucket"
    assert config.bucket == "new-bucket"
    config.description = "test desc"
    assert config.description == "test desc"


async def test_republish_config() -> None:
    r = Republish(source="src.>", destination="dest.>", headers_only=False)
    assert r.source == "src.>"
    assert r.destination == "dest.>"
    assert r.headers_only is False

    r.source = "new.src.>"
    assert r.source == "new.src.>"
    r.destination = "new.dest.>"
    assert r.destination == "new.dest.>"
    r.headers_only = True
    assert r.headers_only is True
