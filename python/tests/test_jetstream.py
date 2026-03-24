import uuid

import pytest
from natsrpy import Nats
from natsrpy.js import (
    JetStream,
    StreamConfig,
)


@pytest.fixture()
async def js(nats: Nats) -> JetStream:
    return await nats.jetstream()


async def test_jetstream_creation(nats: Nats) -> None:
    js = await nats.jetstream()
    assert isinstance(js, JetStream)


async def test_jetstream_has_streams_manager(js: JetStream) -> None:
    assert js.streams is not None


async def test_jetstream_has_kv_manager(js: JetStream) -> None:
    assert js.kv is not None


async def test_jetstream_has_object_store_manager(js: JetStream) -> None:
    assert js.object_store is not None


async def test_jetstream_publish(js: JetStream) -> None:
    stream_name = f"test-js-pub-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"jetstream-msg")
        info = await stream.get_info()
        assert info.state.messages >= 1
    finally:
        await js.streams.delete(stream_name)


async def test_jetstream_publish_str(js: JetStream) -> None:
    stream_name = f"test-js-pubstr-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, "string-payload")
        info = await stream.get_info()
        assert info.state.messages >= 1
    finally:
        await js.streams.delete(stream_name)


async def test_jetstream_publish_with_headers(js: JetStream) -> None:
    stream_name = f"test-js-pubhdr-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    await js.streams.create(config)
    try:
        await js.publish(subj, b"with-headers", headers={"x-test": "value"})
    finally:
        await js.streams.delete(stream_name)
