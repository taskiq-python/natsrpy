import uuid

from natsrpy.js import (
    JetStream,
    PullConsumer,
    PullConsumerConfig,
    PushConsumer,
    PushConsumerConfig,
    StreamConfig,
)


async def test_pull_consumer_name_and_stream(js: JetStream) -> None:
    stream_name = f"test-pcns-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        consumer_name = f"consumer-{uuid.uuid4().hex[:8]}"
        consumer = await stream.consumers.create(
            PullConsumerConfig(name=consumer_name),
        )
        assert isinstance(consumer, PullConsumer)
        assert consumer.name == consumer_name
        assert consumer.stream_name == stream_name
    finally:
        await js.streams.delete(stream_name)


async def test_push_consumer_name_and_stream(js: JetStream) -> None:
    stream_name = f"test-pushns-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        deliver_subj = uuid.uuid4().hex
        consumer_name = f"push-{uuid.uuid4().hex[:8]}"
        consumer = await stream.consumers.create(
            PushConsumerConfig(deliver_subject=deliver_subj, name=consumer_name),
        )
        assert isinstance(consumer, PushConsumer)
        assert consumer.name == consumer_name
        assert consumer.stream_name == stream_name
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_messages_iterator(js: JetStream) -> None:
    stream_name = f"test-pullmsgiter-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"iter-msg-1", wait=True)
        await js.publish(subj, b"iter-msg-2", wait=True)
        consumer = await stream.consumers.create(
            PullConsumerConfig(name=f"consumer-{uuid.uuid4().hex[:8]}"),
        )
        msgs = await consumer.fetch(max_messages=2, timeout=5.0)
        assert len(msgs) == 2
        assert msgs[0].payload == b"iter-msg-1"
        assert msgs[1].payload == b"iter-msg-2"
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_fetch_empty(js: JetStream) -> None:
    stream_name = f"test-fetchempty-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        consumer = await stream.consumers.create(
            PullConsumerConfig(name=f"consumer-{uuid.uuid4().hex[:8]}"),
        )
        msgs = await consumer.fetch(max_messages=1, timeout=0.5)
        assert len(msgs) == 0
    finally:
        await js.streams.delete(stream_name)
