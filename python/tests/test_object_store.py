import io
import uuid

import pytest
from natsrpy import Nats
from natsrpy.js import (
    JetStream,
    ObjectStore,
    ObjectStoreConfig,
    StorageType,
)


@pytest.fixture()
async def js(nats: Nats) -> JetStream:
    return await nats.jetstream()


async def test_object_store_create(js: JetStream) -> None:
    bucket = f"test-os-create-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        assert isinstance(store, ObjectStore)
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_put_and_get(js: JetStream) -> None:
    bucket = f"test-os-pg-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("test-object", b"object-data")
        writer = io.BytesIO()
        await store.get("test-object", writer)
        assert writer.getvalue() == b"object-data"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_put_large(js: JetStream) -> None:
    bucket = f"test-os-large-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        large_data = b"x" * 100000
        await store.put("large-object", large_data)
        writer = io.BytesIO()
        await store.get("large-object", writer)
        assert writer.getvalue() == large_data
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_delete(js: JetStream) -> None:
    bucket = f"test-os-del-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("to-delete", b"delete-me")
        await store.delete("to-delete")
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_put_with_description(js: JetStream) -> None:
    bucket = f"test-os-desc-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put(
            "described-object",
            b"data",
            description="test description",
        )
        writer = io.BytesIO()
        await store.get("described-object", writer)
        assert writer.getvalue() == b"data"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_put_with_headers(js: JetStream) -> None:
    bucket = f"test-os-hdr-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put(
            "header-object",
            b"header-data",
            headers={"x-custom": "value"},
        )
        writer = io.BytesIO()
        await store.get("header-object", writer)
        assert writer.getvalue() == b"header-data"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_overwrite(js: JetStream) -> None:
    bucket = f"test-os-overwrite-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("my-object", b"original")
        await store.put("my-object", b"updated")
        writer = io.BytesIO()
        await store.get("my-object", writer)
        assert writer.getvalue() == b"updated"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_get_existing_bucket(js: JetStream) -> None:
    bucket = f"test-os-getb-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    await js.object_store.create(config)
    try:
        store = await js.object_store.get(bucket)
        assert isinstance(store, ObjectStore)
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_delete_bucket(js: JetStream) -> None:
    bucket = f"test-os-delbucket-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    await js.object_store.create(config)
    await js.object_store.delete(bucket)


async def test_object_store_config_with_options(js: JetStream) -> None:
    bucket = f"test-os-opts-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(
        bucket=bucket,
        description="test object store",
        storage=StorageType.MEMORY,
    )
    store = await js.object_store.create(config)
    try:
        assert isinstance(store, ObjectStore)
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_config_properties() -> None:
    config = ObjectStoreConfig(
        bucket="test-bucket",
        description="test description",
    )
    assert config.bucket == "test-bucket"
    assert config.description == "test description"
