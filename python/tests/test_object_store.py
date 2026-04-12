import asyncio
import io
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from natsrpy.js import (
    JetStream,
    ObjectInfo,
    ObjectInfoIterator,
    ObjectLink,
    ObjectStore,
    ObjectStoreConfig,
    StorageType,
)


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


async def test_object_store_get_info(js: JetStream) -> None:
    bucket = f"test-os-info-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("info-object", b"info-data")
        info = await store.get_info("info-object")
        assert isinstance(info, ObjectInfo)
        assert info.name == "info-object"
        assert info.bucket == bucket
        assert info.size == len(b"info-data")
        assert info.chunks >= 1
        assert isinstance(info.nuid, str)
        assert len(info.nuid) > 0
        assert info.deleted is False
        assert info.digest is not None
        assert isinstance(info.digest, str)
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_get_info_with_description(js: JetStream) -> None:
    bucket = f"test-os-infodesc-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put(
            "desc-object",
            b"data",
            description="my description",
        )
        info = await store.get_info("desc-object")
        assert info.description == "my description"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_get_info_with_headers(js: JetStream) -> None:
    bucket = f"test-os-infohdr-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put(
            "hdr-object",
            b"data",
            headers={"x-test": "hdr-value"},
        )
        info = await store.get_info("hdr-object")
        assert isinstance(info.headers, dict)
        assert "x-test" in info.headers
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_get_info_with_metadata(js: JetStream) -> None:
    bucket = f"test-os-infometa-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put(
            "meta-object",
            b"data",
            metadata={"key1": "val1", "key2": "val2"},
        )
        info = await store.get_info("meta-object")
        assert isinstance(info.metadata, dict)
        assert info.metadata["key1"] == "val1"
        assert info.metadata["key2"] == "val2"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_get_info_modified_time(js: JetStream) -> None:
    bucket = f"test-os-infomod-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("time-object", b"data")
        info = await store.get_info("time-object")
        assert info.modified is not None
        assert isinstance(info.modified, datetime)
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_get_info_no_description(js: JetStream) -> None:
    bucket = f"test-os-infonodesc-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("no-desc-object", b"data")
        info = await store.get_info("no-desc-object")
        assert info.description is None
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_get_info_link_is_none(js: JetStream) -> None:
    bucket = f"test-os-infolink-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("regular-object", b"data")
        info = await store.get_info("regular-object")
        assert info.link is None
    finally:
        await js.object_store.delete(bucket)


async def test_object_info_str(js: JetStream) -> None:
    bucket = f"test-os-str-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("str-object", b"hello")
        info = await store.get_info("str-object")
        result = str(info)
        assert "ObjectInfo" in result
        assert "str-object" in result
        assert bucket in result
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_seal(js: JetStream) -> None:
    bucket = f"test-os-seal-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("seal-object", b"sealed-data")
        await store.seal()
        writer = io.BytesIO()
        await store.get("seal-object", writer)
        assert writer.getvalue() == b"sealed-data"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_list(js: JetStream) -> None:
    bucket = f"test-os-list-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("list-obj-1", b"data1")
        await store.put("list-obj-2", b"data2")
        await store.put("list-obj-3", b"data3")

        iterator = await store.list()
        assert isinstance(iterator, ObjectInfoIterator)

        names = set()
        async for info in iterator:
            assert isinstance(info, ObjectInfo)
            names.add(info.name)

        assert names == {"list-obj-1", "list-obj-2", "list-obj-3"}
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_list_empty(js: JetStream) -> None:
    bucket = f"test-os-listempty-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        iterator = await store.list()
        items = []
        async for info in iterator:
            items.append(info)
        assert items == []
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_list_iterator_next(js: JetStream) -> None:
    bucket = f"test-os-listnext-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("next-obj", b"data")

        iterator = await store.list()
        info = await asyncio.wait_for(anext(iterator), timeout=5.0)
        assert isinstance(info, ObjectInfo)
        assert info.name == "next-obj"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_watch(js: JetStream) -> None:
    bucket = f"test-os-watch-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        watcher = await store.watch()
        assert isinstance(watcher, ObjectInfoIterator)

        await store.put("watch-obj", b"watch-data")

        info = await asyncio.wait_for(anext(watcher), timeout=5.0)
        assert isinstance(info, ObjectInfo)
        assert info.name == "watch-obj"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_watch_with_history(js: JetStream) -> None:
    bucket = f"test-os-watchhist-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("hist-obj-1", b"data1")
        await store.put("hist-obj-2", b"data2")

        watcher = await store.watch(with_history=True)
        info1 = await asyncio.wait_for(anext(watcher), timeout=5.0)
        info2 = await asyncio.wait_for(anext(watcher), timeout=5.0)
        assert {info1.name, info2.name} == {"hist-obj-1", "hist-obj-2"}
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_watch_without_history(js: JetStream) -> None:
    bucket = f"test-os-watchnohist-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("pre-existing", b"data")

        watcher = await store.watch(with_history=False)

        await store.put("new-obj", b"new-data")

        info = await asyncio.wait_for(anext(watcher), timeout=5.0)
        assert info.name == "new-obj"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_link_object(js: JetStream) -> None:
    bucket = f"test-os-linkobj-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("source-obj", b"source-data")
        link_info = await store.link_object("source-obj", "linked-obj")
        assert isinstance(link_info, ObjectInfo)
        assert link_info.name == "linked-obj"
        assert link_info.link is not None
        assert isinstance(link_info.link, ObjectLink)
        assert link_info.link.name == "source-obj"
        assert link_info.link.bucket == bucket
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_link_bucket(js: JetStream) -> None:
    src_bucket = f"test-os-linksrc-{uuid.uuid4().hex[:8]}"
    dest_bucket = f"test-os-linkdest-{uuid.uuid4().hex[:8]}"
    src_config = ObjectStoreConfig(bucket=src_bucket)
    dest_config = ObjectStoreConfig(bucket=dest_bucket)
    await js.object_store.create(src_config)
    dest_store = await js.object_store.create(dest_config)
    try:
        link_info = await dest_store.link_bucket(src_bucket, "bucket-link")
        assert isinstance(link_info, ObjectInfo)
        assert link_info.name == "bucket-link"
        assert link_info.link is not None
        assert isinstance(link_info.link, ObjectLink)
        assert link_info.link.bucket == src_bucket
    finally:
        await js.object_store.delete(src_bucket)
        await js.object_store.delete(dest_bucket)


async def test_object_store_update_metadata(js: JetStream) -> None:
    bucket = f"test-os-updmeta-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("update-obj", b"data")
        updated = await store.update_metadata(
            "update-obj",
            description="new description",
        )
        assert isinstance(updated, ObjectInfo)
        assert updated.description == "new description"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_update_metadata_rename(js: JetStream) -> None:
    bucket = f"test-os-rename-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("old-name", b"data")
        updated = await store.update_metadata("old-name", new_name="new-name")
        assert isinstance(updated, ObjectInfo)
        assert updated.name == "new-name"

        writer = io.BytesIO()
        await store.get("new-name", writer)
        assert writer.getvalue() == b"data"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_update_metadata_with_headers(js: JetStream) -> None:
    bucket = f"test-os-updhdrs-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("hdr-upd-obj", b"data")
        updated = await store.update_metadata(
            "hdr-upd-obj",
            headers={"x-updated": "new-value"},
        )
        assert isinstance(updated, ObjectInfo)
        assert updated.name == "hdr-upd-obj"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_update_metadata_with_metadata(js: JetStream) -> None:
    bucket = f"test-os-updmetadict-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("meta-upd-obj", b"data")
        updated = await store.update_metadata(
            "meta-upd-obj",
            metadata={"meta-key": "meta-val"},
        )
        assert isinstance(updated, ObjectInfo)
        assert updated.name == "meta-upd-obj"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_put_with_metadata(js: JetStream) -> None:
    bucket = f"test-os-putmeta-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put(
            "meta-object",
            b"data",
            metadata={"author": "test-user", "version": "1.0"},
        )
        info = await store.get_info("meta-object")
        assert info.metadata["author"] == "test-user"
        assert info.metadata["version"] == "1.0"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_put_file_str_path(js: JetStream) -> None:
    bucket = f"test-os-putfile-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        file_content = b"file content for testing"
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            await store.put_file("file-object", tmp_path)
            writer = io.BytesIO()
            await store.get("file-object", writer)
            assert writer.getvalue() == file_content
        finally:
            Path(tmp_path).unlink()
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_put_file_path_object(js: JetStream) -> None:
    bucket = f"test-os-putfilepath-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        file_content = b"file content via pathlib"
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file_content)
            tmp_path = Path(tmp.name)

        try:
            await store.put_file("file-object", tmp_path)
            writer = io.BytesIO()
            await store.get("file-object", writer)
            assert writer.getvalue() == file_content
        finally:
            tmp_path.unlink()
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_get_with_chunk_size(js: JetStream) -> None:
    bucket = f"test-os-getchunk-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        data = b"a" * 10000
        await store.put("chunk-object", data)
        writer = io.BytesIO()
        await store.get("chunk-object", writer, chunk_size=1024)
        assert writer.getvalue() == data
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_put_empty_data(js: JetStream) -> None:
    bucket = f"test-os-empty-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("empty-object", b"")
        writer = io.BytesIO()
        await store.get("empty-object", writer)
        assert writer.getvalue() == b""
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_multiple_objects(js: JetStream) -> None:
    bucket = f"test-os-multi-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        objects = {
            "obj-a": b"data-a",
            "obj-b": b"data-b",
            "obj-c": b"data-c",
        }
        for name, data in objects.items():
            await store.put(name, data)

        for name, expected_data in objects.items():
            writer = io.BytesIO()
            await store.get(name, writer)
            assert writer.getvalue() == expected_data
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_delete_then_get_info(js: JetStream) -> None:
    bucket = f"test-os-delinfo-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("to-delete", b"data")
        await store.delete("to-delete")
        info = await store.get_info("to-delete")
        assert info.deleted is True
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_get_nonexistent_raises(js: JetStream) -> None:
    bucket = f"test-os-noexist-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        writer = io.BytesIO()
        with pytest.raises(Exception):
            await store.get("nonexistent-object", writer)
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_get_info_nonexistent_raises(js: JetStream) -> None:
    bucket = f"test-os-noexistinfo-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        with pytest.raises(Exception):
            await store.get_info("nonexistent-object")
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_config_all_options() -> None:
    config = ObjectStoreConfig(
        bucket="full-os",
        description="full config",
        max_age=timedelta(hours=1),
        max_bytes=1048576,
        storage=StorageType.MEMORY,
        num_replicas=1,
        compression=True,
    )
    assert config.bucket == "full-os"
    assert config.description == "full config"
    assert config.max_bytes == 1048576
    assert config.storage == StorageType.MEMORY
    assert config.num_replicas == 1
    assert config.compression is True


async def test_object_store_config_setters() -> None:
    config = ObjectStoreConfig(bucket="original")
    config.bucket = "updated-bucket"
    assert config.bucket == "updated-bucket"
    config.description = "new desc"
    assert config.description == "new desc"
    config.max_bytes = 999
    assert config.max_bytes == 999
    config.num_replicas = 3
    assert config.num_replicas == 3
    config.compression = True
    assert config.compression is True
    config.storage = StorageType.MEMORY
    assert config.storage == StorageType.MEMORY


async def test_object_store_config_defaults() -> None:
    config = ObjectStoreConfig(bucket="defaults")
    assert config.bucket == "defaults"
    assert config.description is None
    assert config.max_bytes == 0
    assert config.num_replicas == 0
    assert config.compression is False
    assert config.placement is None


async def test_object_store_config_with_all_options_create(js: JetStream) -> None:
    bucket = f"test-os-allopts-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(
        bucket=bucket,
        description="full test",
        max_bytes=10485760,
        storage=StorageType.MEMORY,
        num_replicas=1,
        compression=True,
    )
    store = await js.object_store.create(config)
    try:
        assert isinstance(store, ObjectStore)
        await store.put("test-obj", b"data")
        writer = io.BytesIO()
        await store.get("test-obj", writer)
        assert writer.getvalue() == b"data"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_watch_delete_event(js: JetStream) -> None:
    bucket = f"test-os-watchdel-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        watcher = await store.watch()

        await store.put("del-watch-obj", b"data")
        info_put = await asyncio.wait_for(anext(watcher), timeout=5.0)
        assert info_put.name == "del-watch-obj"
        assert info_put.deleted is False

        await store.delete("del-watch-obj")
        info_del = await asyncio.wait_for(anext(watcher), timeout=5.0)
        assert info_del.name == "del-watch-obj"
        assert info_del.deleted is True
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_watch_timeout(js: JetStream) -> None:
    bucket = f"test-os-watchtimeout-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        watcher = await store.watch()
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(anext(watcher), timeout=0.1)
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_list_after_delete(js: JetStream) -> None:
    bucket = f"test-os-listdel-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("keep-obj", b"keep")
        await store.put("del-obj", b"delete")
        await store.delete("del-obj")

        iterator = await store.list()
        names = set()
        async for info in iterator:
            if not info.deleted:
                names.add(info.name)
        assert "keep-obj" in names
        assert "del-obj" not in names
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_put_with_all_options(js: JetStream) -> None:
    bucket = f"test-os-putall-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put(
            "full-object",
            b"full-data",
            description="full description",
            headers={"x-key": "x-value"},
            metadata={"mk": "mv"},
        )
        info = await store.get_info("full-object")
        assert info.name == "full-object"
        assert info.description == "full description"
        assert "x-key" in info.headers
        assert info.metadata["mk"] == "mv"

        writer = io.BytesIO()
        await store.get("full-object", writer)
        assert writer.getvalue() == b"full-data"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_overwrite_preserves_bucket(js: JetStream) -> None:
    bucket = f"test-os-owbucket-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("ow-obj", b"v1")
        await store.put("ow-obj", b"v2")
        info = await store.get_info("ow-obj")
        assert info.bucket == bucket
        assert info.size == 2
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_seal_prevents_put(js: JetStream) -> None:
    bucket = f"test-os-sealput-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.seal()
        with pytest.raises(Exception):
            await store.put("after-seal", b"data")
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_link_object_get_data(js: JetStream) -> None:
    bucket = f"test-os-linkobjget-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("src-obj", b"linked-content")
        await store.link_object("src-obj", "dest-link")

        writer = io.BytesIO()
        await store.get("dest-link", writer)
        assert writer.getvalue() == b"linked-content"
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_get_nonexistent_bucket_raises(js: JetStream) -> None:
    with pytest.raises(Exception):
        await js.object_store.get(f"nonexistent-{uuid.uuid4().hex[:8]}")


async def test_object_store_watch_multiple_events(js: JetStream) -> None:
    bucket = f"test-os-watchmulti-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        watcher = await store.watch()

        await store.put("ev-1", b"d1")
        await store.put("ev-2", b"d2")
        await store.put("ev-3", b"d3")

        names = set()
        for _ in range(3):
            info = await asyncio.wait_for(anext(watcher), timeout=5.0)
            names.add(info.name)
        assert names == {"ev-1", "ev-2", "ev-3"}
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_iterator_aiter_protocol(js: JetStream) -> None:
    bucket = f"test-os-aiter-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put("aiter-obj", b"data")
        iterator = await store.list()
        assert iterator.__aiter__() is iterator
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_put_with_custom_chunk_size(js: JetStream) -> None:
    bucket = f"test-os-putchunk-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        data = b"y" * 50000
        await store.put("chunked-obj", data, chunk_size=8192)
        writer = io.BytesIO()
        await store.get("chunked-obj", writer)
        assert writer.getvalue() == data
    finally:
        await js.object_store.delete(bucket)


async def test_object_store_put_with_multivalue_headers(js: JetStream) -> None:
    bucket = f"test-os-multihdr-{uuid.uuid4().hex[:8]}"
    config = ObjectStoreConfig(bucket=bucket)
    store = await js.object_store.create(config)
    try:
        await store.put(
            "multi-hdr-obj",
            b"data",
            headers={"x-multi": ["val1", "val2"]},
        )
        info = await store.get_info("multi-hdr-obj")
        assert "x-multi" in info.headers
    finally:
        await js.object_store.delete(bucket)
