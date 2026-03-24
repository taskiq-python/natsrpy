import uuid

import pytest
from natsrpy import Nats
from natsrpy.js import (
    JetStream,
    KeyValue,
    KVConfig,
    StorageType,
)


@pytest.fixture()
async def js(nats: Nats) -> JetStream:
    return await nats.jetstream()


async def test_kv_create(js: JetStream) -> None:
    bucket = f"test-kv-create-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        assert isinstance(kv, KeyValue)
        assert kv.name == bucket
    finally:
        await js.kv.delete(bucket)


async def test_kv_put_and_get(js: JetStream) -> None:
    bucket = f"test-kv-pg-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        revision = await kv.put("key1", b"value1")
        assert isinstance(revision, int)
        assert revision >= 1

        value = await kv.get("key1")
        assert value == b"value1"
    finally:
        await js.kv.delete(bucket)


async def test_kv_get_nonexistent(js: JetStream) -> None:
    bucket = f"test-kv-noexist-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        value = await kv.get("nonexistent-key")
        assert value is None
    finally:
        await js.kv.delete(bucket)


async def test_kv_put_overwrite(js: JetStream) -> None:
    bucket = f"test-kv-overwrite-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"original")
        await kv.put("key1", b"updated")
        value = await kv.get("key1")
        assert value == b"updated"
    finally:
        await js.kv.delete(bucket)


async def test_kv_delete_key(js: JetStream) -> None:
    bucket = f"test-kv-delkey-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"to-delete")
        await kv.delete("key1")
        value = await kv.get("key1")
        assert value is None
    finally:
        await js.kv.delete(bucket)


async def test_kv_multiple_keys(js: JetStream) -> None:
    bucket = f"test-kv-multi-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"value1")
        await kv.put("key2", b"value2")
        await kv.put("key3", b"value3")
        assert await kv.get("key1") == b"value1"
        assert await kv.get("key2") == b"value2"
        assert await kv.get("key3") == b"value3"
    finally:
        await js.kv.delete(bucket)


async def test_kv_large_value(js: JetStream) -> None:
    bucket = f"test-kv-large-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        large_value = b"x" * 65536
        await kv.put("large", large_value)
        value = await kv.get("large")
        assert value == large_value
    finally:
        await js.kv.delete(bucket)


async def test_kv_properties(js: JetStream) -> None:
    bucket = f"test-kv-props-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        assert kv.name == bucket
        assert isinstance(kv.stream_name, str)
        assert len(kv.stream_name) > 0
        assert isinstance(kv.prefix, str)
        assert isinstance(kv.use_jetstream_prefix, bool)
    finally:
        await js.kv.delete(bucket)


async def test_kv_create_or_update(js: JetStream) -> None:
    bucket = f"test-kv-cou-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv1 = await js.kv.create_or_update(config)
    try:
        assert isinstance(kv1, KeyValue)
        config.description = "updated"
        kv2 = await js.kv.create_or_update(config)
        assert isinstance(kv2, KeyValue)
    finally:
        await js.kv.delete(bucket)


async def test_kv_get_bucket(js: JetStream) -> None:
    bucket = f"test-kv-getb-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    await js.kv.create(config)
    try:
        kv = await js.kv.get(bucket)
        assert isinstance(kv, KeyValue)
        assert kv.name == bucket
    finally:
        await js.kv.delete(bucket)


async def test_kv_delete_bucket(js: JetStream) -> None:
    bucket = f"test-kv-delbucket-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    await js.kv.create(config)
    result = await js.kv.delete(bucket)
    assert result is True


async def test_kv_config_with_options(js: JetStream) -> None:
    bucket = f"test-kv-opts-{uuid.uuid4().hex[:8]}"
    config = KVConfig(
        bucket=bucket,
        description="test kv store",
        history=5,
        storage=StorageType.MEMORY,
    )
    kv = await js.kv.create(config)
    try:
        assert kv.name == bucket
    finally:
        await js.kv.delete(bucket)


async def test_kv_config_properties() -> None:
    config = KVConfig(
        bucket="test-bucket",
        description="test description",
        history=10,
    )
    assert config.bucket == "test-bucket"
    assert config.description == "test description"
    assert config.history == 10
