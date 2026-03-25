import uuid

from natsrpy.js import (
    DiscardPolicy,
    JetStream,
    RetentionPolicy,
    StorageType,
    Stream,
    StreamConfig,
)


async def test_stream_create(js: JetStream) -> None:
    name = f"test-create-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    stream = await js.streams.create(config)
    try:
        assert isinstance(stream, Stream)
    finally:
        await js.streams.delete(name)


async def test_stream_get(js: JetStream) -> None:
    name = f"test-get-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    await js.streams.create(config)
    try:
        stream = await js.streams.get(name)
        assert isinstance(stream, Stream)
    finally:
        await js.streams.delete(name)


async def test_stream_delete(js: JetStream) -> None:
    name = f"test-del-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    await js.streams.create(config)
    result = await js.streams.delete(name)
    assert result is True


async def test_stream_create_or_update(js: JetStream) -> None:
    name = f"test-cou-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    stream = await js.streams.create_or_update(config)
    try:
        assert isinstance(stream, Stream)
        config.description = "updated"
        stream2 = await js.streams.create_or_update(config)
        assert isinstance(stream2, Stream)
    finally:
        await js.streams.delete(name)


async def test_stream_update(js: JetStream) -> None:
    name = f"test-upd-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    await js.streams.create(config)
    try:
        config.description = "updated description"
        stream = await js.streams.update(config)
        assert isinstance(stream, Stream)
        info = await stream.get_info()
        assert info.config.description == "updated description"
    finally:
        await js.streams.delete(name)


async def test_stream_info(js: JetStream) -> None:
    name = f"test-info-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    stream = await js.streams.create(config)
    try:
        info = await stream.get_info()
        assert info.config.name == name
        assert info.state.messages == 0
        assert info.state.bytes == 0
        assert info.state.consumer_count == 0
        assert str(info) is not None
    finally:
        await js.streams.delete(name)


async def test_stream_purge(js: JetStream) -> None:
    name = f"test-purge-{uuid.uuid4().hex[:8]}"
    subj = f"{name}.data"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"msg-1", wait=True)
        await js.publish(subj, b"msg-2", wait=True)
        await js.publish(subj, b"msg-3", wait=True)
        info = await stream.get_info()
        assert info.state.messages == 3
        purged = await stream.purge()
        assert purged == 3
        info = await stream.get_info()
        assert info.state.messages == 0
    finally:
        await js.streams.delete(name)


async def test_stream_purge_with_filter(js: JetStream) -> None:
    name = f"test-purgef-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(f"{name}.a", b"a-msg", wait=True)
        await js.publish(f"{name}.b", b"b-msg", wait=True)
        purged = await stream.purge(filter=f"{name}.a")
        assert purged == 1
        info = await stream.get_info()
        assert info.state.messages == 1
    finally:
        await js.streams.delete(name)


async def test_stream_direct_get(js: JetStream) -> None:
    name = f"test-dget-{uuid.uuid4().hex[:8]}"
    subj = f"{name}.data"
    config = StreamConfig(name=name, subjects=[f"{name}.>"], allow_direct=True)
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"direct-get-msg", wait=True)
        msg = await stream.direct_get(sequence=1)
        assert msg.payload == b"direct-get-msg"
        assert msg.subject == subj
        assert msg.sequence == 1
    finally:
        await js.streams.delete(name)


async def test_stream_message_repr(js: JetStream) -> None:
    name = f"test-smrepr-{uuid.uuid4().hex[:8]}"
    subj = f"{name}.data"
    config = StreamConfig(name=name, subjects=[f"{name}.>"], allow_direct=True)
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"repr-test", wait=True)
        msg = await stream.direct_get(sequence=1)
        r = repr(msg)
        assert isinstance(r, str)
        assert len(r) > 0
    finally:
        await js.streams.delete(name)


async def test_stream_config_memory_storage(js: JetStream) -> None:
    name = f"test-mem-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(
        name=name,
        subjects=[f"{name}.>"],
        storage=StorageType.MEMORY,
    )
    stream = await js.streams.create(config)
    try:
        info = await stream.get_info()
        assert info.config.storage == StorageType.MEMORY
    finally:
        await js.streams.delete(name)


async def test_stream_config_retention_policy(js: JetStream) -> None:
    name = f"test-ret-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(
        name=name,
        subjects=[f"{name}.>"],
        retention=RetentionPolicy.INTEREST,
    )
    stream = await js.streams.create(config)
    try:
        info = await stream.get_info()
        assert info.config.retention == RetentionPolicy.INTEREST
    finally:
        await js.streams.delete(name)


async def test_stream_config_discard_policy(js: JetStream) -> None:
    name = f"test-disc-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(
        name=name,
        subjects=[f"{name}.>"],
        max_messages=100,
        discard=DiscardPolicy.NEW,
    )
    stream = await js.streams.create(config)
    try:
        info = await stream.get_info()
        assert info.config.discard == DiscardPolicy.NEW
    finally:
        await js.streams.delete(name)


async def test_stream_config_max_settings(js: JetStream) -> None:
    name = f"test-max-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(
        name=name,
        subjects=[f"{name}.>"],
        max_bytes=1048576,
        max_messages=1000,
        max_messages_per_subject=100,
        max_message_size=4096,
    )
    stream = await js.streams.create(config)
    try:
        info = await stream.get_info()
        assert info.config.max_bytes == 1048576
        assert info.config.max_messages == 1000
        assert info.config.max_messages_per_subject == 100
        assert info.config.max_message_size == 4096
    finally:
        await js.streams.delete(name)


async def test_stream_config_description(js: JetStream) -> None:
    name = f"test-desc-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(
        name=name,
        subjects=[f"{name}.>"],
        description="A test stream",
    )
    stream = await js.streams.create(config)
    try:
        info = await stream.get_info()
        assert info.config.description == "A test stream"
    finally:
        await js.streams.delete(name)


async def test_stream_consumers_manager(js: JetStream) -> None:
    name = f"test-cmgr-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    stream = await js.streams.create(config)
    try:
        assert stream.consumers is not None
    finally:
        await js.streams.delete(name)


async def test_stream_state_after_publish(js: JetStream) -> None:
    name = f"test-state-{uuid.uuid4().hex[:8]}"
    subj = f"{name}.data"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"msg-1", wait=True)
        await js.publish(subj, b"msg-2", wait=True)
        info = await stream.get_info()
        assert info.state.messages == 2
        assert info.state.first_sequence == 1
        assert info.state.last_sequence == 2
        assert info.state.bytes > 0
    finally:
        await js.streams.delete(name)
