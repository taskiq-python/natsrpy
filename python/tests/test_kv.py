import asyncio
import uuid
from datetime import datetime, timedelta

import pytest
from natsrpy.js import (
    JetStream,
    KeysIterator,
    KeyValue,
    KVConfig,
    KVEntry,
    KVEntryIterator,
    KVOperation,
    KVStatus,
    StorageType,
    StreamInfo,
)


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


# ---------------------------------------------------------------------------
# kv.create
# ---------------------------------------------------------------------------


async def test_kv_create_key(js: JetStream) -> None:
    bucket = f"test-kv-createkey-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        revision = await kv.create("key1", b"initial")
        assert isinstance(revision, int)
        assert revision >= 1

        # Value should be retrievable
        value = await kv.get("key1")
        assert value == b"initial"
    finally:
        await js.kv.delete(bucket)


async def test_kv_create_key_already_exists_raises(js: JetStream) -> None:
    bucket = f"test-kv-createexists-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        await kv.create("dup", b"first")
        with pytest.raises(Exception):
            await kv.create("dup", b"second")
    finally:
        await js.kv.delete(bucket)


async def test_kv_create_key_with_ttl(js: JetStream) -> None:
    bucket = f"test-kv-createttl-{uuid.uuid4().hex[:8]}"
    # limit_markers enables per-message TTL support on the bucket
    config = KVConfig(bucket=bucket, limit_markers=timedelta(hours=24))
    kv = await js.kv.create(config)
    try:
        revision = await kv.create("ttl-key", b"ttl-value", ttl=timedelta(hours=1))
        assert isinstance(revision, int)
        assert revision >= 1
    finally:
        await js.kv.delete(bucket)


async def test_kv_create_key_with_ttl_float(js: JetStream) -> None:
    bucket = f"test-kv-createttlf-{uuid.uuid4().hex[:8]}"
    # limit_markers enables per-message TTL support on the bucket
    config = KVConfig(bucket=bucket, limit_markers=timedelta(hours=24))
    kv = await js.kv.create(config)
    try:
        revision = await kv.create("ttl-key-f", b"ttl-value-f", ttl=3600.0)
        assert isinstance(revision, int)
        assert revision >= 1
    finally:
        await js.kv.delete(bucket)


# ---------------------------------------------------------------------------
# kv.update
# ---------------------------------------------------------------------------


async def test_kv_update(js: JetStream) -> None:
    bucket = f"test-kv-update-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        revision = await kv.put("key1", b"original")
        await kv.update("key1", b"updated", revision)

        value = await kv.get("key1")
        assert value == b"updated"
    finally:
        await js.kv.delete(bucket)


async def test_kv_update_wrong_revision_raises(js: JetStream) -> None:
    bucket = f"test-kv-updaterev-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"original")
        with pytest.raises(Exception):
            await kv.update("key1", b"bad-update", revision=9999)
    finally:
        await js.kv.delete(bucket)


# ---------------------------------------------------------------------------
# kv.delete with expect_revision
# ---------------------------------------------------------------------------


async def test_kv_delete_with_expect_revision(js: JetStream) -> None:
    bucket = f"test-kv-delrev-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        revision = await kv.put("key1", b"value")
        await kv.delete("key1", expect_revision=revision)
        value = await kv.get("key1")
        assert value is None
    finally:
        await js.kv.delete(bucket)


async def test_kv_delete_wrong_revision_raises(js: JetStream) -> None:
    bucket = f"test-kv-delwrongrev-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"value")
        with pytest.raises(Exception):
            await kv.delete("key1", expect_revision=9999)
    finally:
        await js.kv.delete(bucket)


# ---------------------------------------------------------------------------
# kv.purge
# ---------------------------------------------------------------------------


async def test_kv_purge(js: JetStream) -> None:
    bucket = f"test-kv-purge-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"value1")
        await kv.put("key1", b"value2")
        await kv.purge("key1")
        value = await kv.get("key1")
        assert value is None
    finally:
        await js.kv.delete(bucket)


async def test_kv_purge_with_ttl(js: JetStream) -> None:
    bucket = f"test-kv-purgettl-{uuid.uuid4().hex[:8]}"
    # limit_markers enables per-message TTL support on the bucket
    config = KVConfig(bucket=bucket, limit_markers=timedelta(hours=24))
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"value")
        await kv.purge("key1", ttl=timedelta(hours=1))
        value = await kv.get("key1")
        assert value is None
    finally:
        await js.kv.delete(bucket)


async def test_kv_purge_with_expect_revision(js: JetStream) -> None:
    bucket = f"test-kv-purgerev-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        revision = await kv.put("key1", b"value")
        await kv.purge("key1", expect_revision=revision)
        value = await kv.get("key1")
        assert value is None
    finally:
        await js.kv.delete(bucket)


async def test_kv_purge_with_ttl_and_expect_revision(js: JetStream) -> None:
    bucket = f"test-kv-purgettlrev-{uuid.uuid4().hex[:8]}"
    # limit_markers enables per-message TTL support on the bucket
    config = KVConfig(bucket=bucket, limit_markers=timedelta(hours=24))
    kv = await js.kv.create(config)
    try:
        revision = await kv.put("key1", b"value")
        await kv.purge("key1", ttl=timedelta(hours=1), expect_revision=revision)
        value = await kv.get("key1")
        assert value is None
    finally:
        await js.kv.delete(bucket)


async def test_kv_purge_wrong_revision_raises(js: JetStream) -> None:
    bucket = f"test-kv-purgewrongrev-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"value")
        with pytest.raises(Exception):
            await kv.purge("key1", expect_revision=9999)
    finally:
        await js.kv.delete(bucket)


# ---------------------------------------------------------------------------
# kv.entry
# ---------------------------------------------------------------------------


async def test_kv_entry(js: JetStream) -> None:
    bucket = f"test-kv-entry-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"hello")
        entry = await kv.entry("key1")
        assert isinstance(entry, KVEntry)
        assert entry.bucket == bucket
        assert entry.key == "key1"
        assert bytes(entry.value) == b"hello"
        assert isinstance(entry.revision, int)
        assert entry.revision >= 1
        assert isinstance(entry.delta, int)
        assert isinstance(entry.created, datetime)
        assert entry.operation == KVOperation.Put
        assert isinstance(entry.seen_current, bool)
    finally:
        await js.kv.delete(bucket)


async def test_kv_entry_nonexistent_returns_none(js: JetStream) -> None:
    bucket = f"test-kv-entrynone-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        entry = await kv.entry("missing-key")
        assert entry is None
    finally:
        await js.kv.delete(bucket)


async def test_kv_entry_for_revision(js: JetStream) -> None:
    bucket = f"test-kv-entryrev-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket, history=5)
    kv = await js.kv.create(config)
    try:
        rev1 = await kv.put("key1", b"first")
        await kv.put("key1", b"second")

        entry = await kv.entry("key1", revision=rev1)
        assert isinstance(entry, KVEntry)
        assert bytes(entry.value) == b"first"
        assert entry.revision == rev1
    finally:
        await js.kv.delete(bucket)


async def test_kv_entry_operation_delete(js: JetStream) -> None:
    bucket = f"test-kv-entrydelop-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket, history=5)
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"value")
        await kv.delete("key1")
        entry = await kv.entry("key1")
        assert entry is not None
        assert entry.operation == KVOperation.Delete
    finally:
        await js.kv.delete(bucket)


async def test_kv_entry_operation_purge(js: JetStream) -> None:
    bucket = f"test-kv-entrypurgeop-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket, history=5)
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"value")
        await kv.purge("key1")
        entry = await kv.entry("key1")
        assert entry is not None
        assert entry.operation == KVOperation.Purge
    finally:
        await js.kv.delete(bucket)


# ---------------------------------------------------------------------------
# kv.status
# ---------------------------------------------------------------------------


async def test_kv_status(js: JetStream) -> None:
    bucket = f"test-kv-status-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        status = await kv.status()
        assert isinstance(status, KVStatus)
        assert status.bucket == bucket
        assert isinstance(status.info, StreamInfo)
    finally:
        await js.kv.delete(bucket)


# ---------------------------------------------------------------------------
# kv.keys
# ---------------------------------------------------------------------------


async def test_kv_keys(js: JetStream) -> None:
    bucket = f"test-kv-keys-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        await kv.put("alpha", b"1")
        await kv.put("beta", b"2")
        await kv.put("gamma", b"3")

        keys_iter = await kv.keys()
        assert isinstance(keys_iter, KeysIterator)

        collected: list[str] = []
        async for key in keys_iter:
            collected.append(key)

        assert sorted(collected) == ["alpha", "beta", "gamma"]
    finally:
        await js.kv.delete(bucket)


async def test_kv_keys_empty_bucket(js: JetStream) -> None:
    bucket = f"test-kv-keysempty-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        keys_iter = await kv.keys()
        assert isinstance(keys_iter, KeysIterator)
        collected: list[str] = []
        async for key in keys_iter:
            collected.append(key)
        assert collected == []
    finally:
        await js.kv.delete(bucket)


async def test_kv_keys_iterator_next_with_timeout(js: JetStream) -> None:
    bucket = f"test-kv-keysnext-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        await kv.put("k1", b"v1")
        keys_iter = await kv.keys()
        key = await asyncio.wait_for(anext(keys_iter), timeout=0.5)
        assert isinstance(key, str)
        assert key == "k1"
    finally:
        await js.kv.delete(bucket)


async def test_kv_keys_iterator_next_timeout_timedelta(js: JetStream) -> None:
    bucket = f"test-kv-keystd-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        await kv.put("k1", b"v1")
        keys_iter = await kv.keys()
        key = await asyncio.wait_for(anext(keys_iter), timeout=0.5)
        assert isinstance(key, str)
        assert key == "k1"
    finally:
        await js.kv.delete(bucket)


# ---------------------------------------------------------------------------
# kv.history
# ---------------------------------------------------------------------------


async def test_kv_history(js: JetStream) -> None:
    bucket = f"test-kv-history-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket, history=10)
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"v1")
        await kv.put("key1", b"v2")
        await kv.put("key1", b"v3")

        history_iter = await kv.history("key1")
        assert isinstance(history_iter, KVEntryIterator)

        entries: list[KVEntry] = []
        async for entry in history_iter:
            entries.append(entry)

        assert len(entries) == 3
        assert bytes(entries[0].value) == b"v1"
        assert bytes(entries[1].value) == b"v2"
        assert bytes(entries[2].value) == b"v3"
        for entry in entries:
            assert entry.key == "key1"
            assert entry.bucket == bucket
    finally:
        await js.kv.delete(bucket)


async def test_kv_history_iterator_next_with_timeout(js: JetStream) -> None:
    bucket = f"test-kv-histnext-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket, history=5)
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"value")
        history_iter = await kv.history("key1")
        entry = await asyncio.wait_for(anext(history_iter), timeout=0.5)
        assert isinstance(entry, KVEntry)
        assert bytes(entry.value) == b"value"
    finally:
        await js.kv.delete(bucket)


async def test_kv_history_iterator_next_with_timedelta(js: JetStream) -> None:
    bucket = f"test-kv-histtd-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket, history=5)
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"value")
        history_iter = await kv.history("key1")
        entry = await asyncio.wait_for(anext(history_iter), timeout=0.5)
        assert isinstance(entry, KVEntry)
        assert bytes(entry.value) == b"value"
    finally:
        await js.kv.delete(bucket)


# ---------------------------------------------------------------------------
# kv.watch_all
# ---------------------------------------------------------------------------


async def test_kv_watch_all(js: JetStream) -> None:
    bucket = f"test-kv-watchall-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        watcher = await kv.watch_all()
        assert isinstance(watcher, KVEntryIterator)

        await kv.put("w1", b"val1")

        entry = await asyncio.wait_for(anext(watcher), timeout=0.5)
        assert isinstance(entry, KVEntry)
        assert entry.key == "w1"
        assert bytes(entry.value) == b"val1"
    finally:
        await js.kv.delete(bucket)


async def test_kv_watch_all_from_revision(js: JetStream) -> None:
    bucket = f"test-kv-watchallrev-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        rev1 = await kv.put("k1", b"first")
        await kv.put("k2", b"second")

        watcher = await kv.watch_all(from_revision=rev1)
        assert isinstance(watcher, KVEntryIterator)

        entry1 = await asyncio.wait_for(anext(watcher), timeout=0.5)
        assert isinstance(entry1, KVEntry)
    finally:
        await js.kv.delete(bucket)


async def test_kv_watch_all_timeout(js: JetStream) -> None:
    bucket = f"test-kv-watchalltout-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        watcher = await kv.watch_all()
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(anext(watcher), timeout=0.1)
    finally:
        await js.kv.delete(bucket)


# ---------------------------------------------------------------------------
# kv.watch
# ---------------------------------------------------------------------------


async def test_kv_watch(js: JetStream) -> None:
    bucket = f"test-kv-watch-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        watcher = await kv.watch("watched-key")
        assert isinstance(watcher, KVEntryIterator)

        await kv.put("watched-key", b"watch-val")

        entry = await asyncio.wait_for(anext(watcher), timeout=0.5)
        assert isinstance(entry, KVEntry)
        assert entry.key == "watched-key"
        assert bytes(entry.value) == b"watch-val"
    finally:
        await js.kv.delete(bucket)


async def test_kv_watch_from_revision(js: JetStream) -> None:
    bucket = f"test-kv-watchrev-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket, history=5)
    kv = await js.kv.create(config)
    try:
        rev1 = await kv.put("wkey", b"old")
        await kv.put("wkey", b"new")

        watcher = await kv.watch("wkey", from_revision=rev1)
        assert isinstance(watcher, KVEntryIterator)

        entry = await asyncio.wait_for(anext(watcher), timeout=5.0)
        assert isinstance(entry, KVEntry)
    finally:
        await js.kv.delete(bucket)


async def test_kv_watch_timeout(js: JetStream) -> None:
    bucket = f"test-kv-watchtout-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        watcher = await kv.watch("nonexistent")
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(anext(watcher), timeout=0.1)
    finally:
        await js.kv.delete(bucket)


# ---------------------------------------------------------------------------
# kv.watch_with_history
# ---------------------------------------------------------------------------


async def test_kv_watch_with_history(js: JetStream) -> None:
    bucket = f"test-kv-watchhist-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket, history=10)
    kv = await js.kv.create(config)
    try:
        await kv.put("hkey", b"h1")
        await kv.put("hkey", b"h2")

        # watch_with_history uses DeliverPolicy::LastPerSubject, so it delivers
        # only the LATEST value per key, then watches for new updates.
        watcher = await kv.watch_with_history("hkey")
        assert isinstance(watcher, KVEntryIterator)

        entry = await asyncio.wait_for(anext(watcher), timeout=5.0)
        assert bytes(entry.value) == b"h2"

        # Further puts are also received
        await kv.put("hkey", b"h3")
        entry_new = await asyncio.wait_for(anext(watcher), timeout=5.0)
        assert bytes(entry_new.value) == b"h3"
    finally:
        await js.kv.delete(bucket)


# ---------------------------------------------------------------------------
# kv.watch_many
# ---------------------------------------------------------------------------


async def test_kv_watch_many(js: JetStream) -> None:
    bucket = f"test-kv-watchmany-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        watcher = await kv.watch_many(["mk1", "mk2"])
        assert isinstance(watcher, KVEntryIterator)

        await kv.put("mk1", b"val1")

        entry = await asyncio.wait_for(anext(watcher), timeout=5.0)
        assert isinstance(entry, KVEntry)
        assert entry.key == "mk1"
        assert bytes(entry.value) == b"val1"
    finally:
        await js.kv.delete(bucket)


async def test_kv_watch_many_with_history(js: JetStream) -> None:
    bucket = f"test-kv-watchmanyhist-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket, history=10)
    kv = await js.kv.create(config)
    try:
        await kv.put("mk1", b"val1")
        await kv.put("mk2", b"val2")

        watcher = await kv.watch_many_with_history(["mk1", "mk2"])
        assert isinstance(watcher, KVEntryIterator)

        entry1 = await asyncio.wait_for(anext(watcher), timeout=5.0)
        entry2 = await asyncio.wait_for(anext(watcher), timeout=5.0)
        assert isinstance(entry1, KVEntry)
        assert isinstance(entry2, KVEntry)
        collected_keys = {entry1.key, entry2.key}
        assert collected_keys == {"mk1", "mk2"}
    finally:
        await js.kv.delete(bucket)


# ---------------------------------------------------------------------------
# KVOperation enum
# ---------------------------------------------------------------------------


async def test_kv_operation_put_value(js: JetStream) -> None:
    bucket = f"test-kv-opput-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"v")
        entry = await kv.entry("key1")
        assert entry is not None
        assert entry.operation == KVOperation.Put
    finally:
        await js.kv.delete(bucket)


async def test_kv_operation_delete_value(js: JetStream) -> None:
    bucket = f"test-kv-opdel-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket, history=5)
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"v")
        await kv.delete("key1")
        entry = await kv.entry("key1")
        assert entry is not None
        assert entry.operation == KVOperation.Delete
    finally:
        await js.kv.delete(bucket)


async def test_kv_operation_purge_value(js: JetStream) -> None:
    bucket = f"test-kv-oppurge-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket, history=5)
    kv = await js.kv.create(config)
    try:
        await kv.put("key1", b"v")
        await kv.purge("key1")
        entry = await kv.entry("key1")
        assert entry is not None
        assert entry.operation == KVOperation.Purge
    finally:
        await js.kv.delete(bucket)


async def test_kv_operation_equality() -> None:
    assert KVOperation.Put == KVOperation.Put
    assert KVOperation.Delete == KVOperation.Delete
    assert KVOperation.Purge == KVOperation.Purge
    assert KVOperation.Put != KVOperation.Delete
    assert KVOperation.Put != KVOperation.Purge
    assert KVOperation.Delete != KVOperation.Purge


async def test_kv_entry_seen_current(js: JetStream) -> None:
    bucket = f"test-kv-seen-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket)
    kv = await js.kv.create(config)
    try:
        # Create watcher on empty bucket, then put — the received entry is a live update
        watcher = await kv.watch_all()
        await kv.put("mykey", b"value1")
        entry = await asyncio.wait_for(anext(watcher), timeout=5.0)
        assert isinstance(entry.seen_current, bool)
        # First live update on an empty bucket is marked as seen_current
        assert entry.seen_current is True
    finally:
        await js.kv.delete(bucket)


async def test_kv_config_max_age_timedelta(js: JetStream) -> None:
    bucket = f"test-kv-maxage-{uuid.uuid4().hex[:8]}"
    max_age = timedelta(hours=1)
    config = KVConfig(bucket=bucket, max_age=max_age)
    assert config.max_age == max_age
    kv = await js.kv.create(config)
    try:
        assert kv is not None
    finally:
        await js.kv.delete(bucket)


async def test_kv_config_description_none() -> None:
    config = KVConfig(bucket="test-desc-none")
    assert config.description is None


async def test_kv_config_description_set() -> None:
    config = KVConfig(bucket="test-desc-set", description="my description")
    assert config.description == "my description"
