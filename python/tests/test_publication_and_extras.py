import uuid

from natsrpy import Nats
from natsrpy.js import JetStream, Publication, StreamConfig


async def test_publication_properties(js: JetStream) -> None:
    stream_name = f"test-pub-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    await js.streams.create(config)
    try:
        pub = await js.publish(subj, b"pub-test", wait=True)
        assert isinstance(pub, Publication)
        assert pub.stream == stream_name
        assert pub.sequence >= 1
        assert isinstance(pub.domain, str)
        assert isinstance(pub.duplicate, bool)
        assert pub.duplicate is False
    finally:
        await js.streams.delete(stream_name)


async def test_publication_value_none(js: JetStream) -> None:
    stream_name = f"test-pubval-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    await js.streams.create(config)
    try:
        pub = await js.publish(subj, b"val-test", wait=True)
        # value is only set for counters, None for regular streams
        assert pub.value is None
    finally:
        await js.streams.delete(stream_name)


async def test_subscribe_with_queue_group(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    queue = f"queue-{uuid.uuid4().hex[:8]}"
    sub = await nats.subscribe(subject=subj, queue=queue)
    await nats.publish(subj, b"queue-msg")
    msg = await sub.next(timeout=5.0)
    assert msg.payload == b"queue-msg"
    await sub.unsubscribe()


async def test_nats_publish_bytearray(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    payload = bytearray(b"bytearray-payload")
    sub = await nats.subscribe(subject=subj)
    await nats.publish(subj, payload)
    msg = await anext(sub)
    assert msg.payload == bytes(payload)


async def test_nats_publish_memoryview(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    data = b"memoryview-payload"
    payload = memoryview(data)
    sub = await nats.subscribe(subject=subj)
    await nats.publish(subj, payload)
    msg = await anext(sub)
    assert msg.payload == data
