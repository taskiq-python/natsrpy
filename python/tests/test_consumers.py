import uuid

import pytest
from natsrpy import Nats
from natsrpy.js import (
    AckPolicy,
    DeliverPolicy,
    JetStream,
    PullConsumer,
    PullConsumerConfig,
    PushConsumer,
    PushConsumerConfig,
    ReplayPolicy,
    StreamConfig,
)


@pytest.fixture()
async def js(nats: Nats) -> JetStream:
    return await nats.jetstream()


async def test_pull_consumer_create(js: JetStream) -> None:
    stream_name = f"test-pcreate-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4().hex[:8]}",
        )
        consumer = await stream.consumers.create(consumer_config)
        assert isinstance(consumer, PullConsumer)
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_fetch(js: JetStream) -> None:
    stream_name = f"test-pfetch-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"fetch-msg-1")
        await js.publish(subj, b"fetch-msg-2")

        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4().hex[:8]}",
        )
        consumer = await stream.consumers.create(consumer_config)
        messages = await consumer.fetch(max_messages=2, timeout=5.0)
        assert len(messages) == 2
        assert messages[0].payload == b"fetch-msg-1"
        assert messages[1].payload == b"fetch-msg-2"
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_fetch_with_ack(js: JetStream) -> None:
    stream_name = f"test-pack-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"ack-msg")

        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4().hex[:8]}",
            ack_policy=AckPolicy.EXPLICIT,
        )
        consumer = await stream.consumers.create(consumer_config)
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        await messages[0].ack()
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_nack(js: JetStream) -> None:
    stream_name = f"test-pnack-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"nack-msg")

        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4().hex[:8]}",
            ack_policy=AckPolicy.EXPLICIT,
        )
        consumer = await stream.consumers.create(consumer_config)
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        await messages[0].nack()
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_term(js: JetStream) -> None:
    stream_name = f"test-pterm-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"term-msg")

        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4().hex[:8]}",
            ack_policy=AckPolicy.EXPLICIT,
        )
        consumer = await stream.consumers.create(consumer_config)
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        await messages[0].term()
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_progress(js: JetStream) -> None:
    stream_name = f"test-pprog-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"progress-msg")

        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4().hex[:8]}",
            ack_policy=AckPolicy.EXPLICIT,
        )
        consumer = await stream.consumers.create(consumer_config)
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        await messages[0].progress()
        await messages[0].ack()
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_message_properties(js: JetStream) -> None:
    stream_name = f"test-pmsgprop-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"prop-msg")

        consumer_name = f"consumer-{uuid.uuid4().hex[:8]}"
        consumer_config = PullConsumerConfig(name=consumer_name)
        consumer = await stream.consumers.create(consumer_config)
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        msg = messages[0]
        assert msg.subject == subj
        assert msg.payload == b"prop-msg"
        assert msg.stream == stream_name
        assert msg.consumer == consumer_name
        assert msg.stream_sequence == 1
        assert msg.consumer_sequence == 1
        assert msg.delivered >= 1
        assert msg.pending >= 0
        assert msg.published is not None
        r = repr(msg)
        assert isinstance(r, str)
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_with_filter_subject(js: JetStream) -> None:
    stream_name = f"test-pfilter-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(f"{stream_name}.a", b"msg-a")
        await js.publish(f"{stream_name}.b", b"msg-b")

        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4().hex[:8]}",
            filter_subject=f"{stream_name}.a",
        )
        consumer = await stream.consumers.create(consumer_config)
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        assert messages[0].payload == b"msg-a"
        await messages[0].ack()
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_deliver_policy(js: JetStream) -> None:
    stream_name = f"test-pdeliver-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"old-msg")
        await js.publish(subj, b"new-msg")

        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4().hex[:8]}",
            deliver_policy=DeliverPolicy.LAST,
        )
        consumer = await stream.consumers.create(consumer_config)
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        assert messages[0].payload == b"new-msg"
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_replay_policy(js: JetStream) -> None:
    stream_name = f"test-preplay-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4().hex[:8]}",
            replay_policy=ReplayPolicy.INSTANT,
        )
        consumer = await stream.consumers.create(consumer_config)
        assert isinstance(consumer, PullConsumer)
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_durable(js: JetStream) -> None:
    stream_name = f"test-pdurable-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        durable_name = f"durable-{uuid.uuid4().hex[:8]}"
        consumer_config = PullConsumerConfig(
            durable_name=durable_name,
        )
        consumer = await stream.consumers.create(consumer_config)
        assert isinstance(consumer, PullConsumer)

        consumer2 = await stream.consumers.get_pull(durable_name)
        assert isinstance(consumer2, PullConsumer)
    finally:
        await js.streams.delete(stream_name)


async def test_push_consumer_create(js: JetStream) -> None:
    stream_name = f"test-pushcreate-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        deliver_subj = uuid.uuid4().hex
        consumer_config = PushConsumerConfig(
            deliver_subject=deliver_subj,
            name=f"consumer-{uuid.uuid4().hex[:8]}",
        )
        consumer = await stream.consumers.create(consumer_config)
        assert isinstance(consumer, PushConsumer)
    finally:
        await js.streams.delete(stream_name)


async def test_push_consumer_messages(js: JetStream) -> None:
    stream_name = f"test-pushmsg-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"push-msg-1")
        await js.publish(subj, b"push-msg-2")

        deliver_subj = uuid.uuid4().hex
        consumer_config = PushConsumerConfig(
            deliver_subject=deliver_subj,
            name=f"consumer-{uuid.uuid4().hex[:8]}",
        )
        consumer = await stream.consumers.create(consumer_config)
        msgs_iter = await consumer.messages()
        msg1 = await msgs_iter.next(timeout=5.0)
        msg2 = await msgs_iter.next(timeout=5.0)
        assert msg1.payload == b"push-msg-1"
        assert msg2.payload == b"push-msg-2"
    finally:
        await js.streams.delete(stream_name)


async def test_consumer_config_properties() -> None:
    config = PullConsumerConfig(
        name="test-consumer",
        description="test description",
        ack_policy=AckPolicy.EXPLICIT,
        deliver_policy=DeliverPolicy.ALL,
        replay_policy=ReplayPolicy.INSTANT,
        max_deliver=5,
        max_ack_pending=100,
    )
    assert config.name == "test-consumer"
    assert config.description == "test description"
    assert config.ack_policy == AckPolicy.EXPLICIT
    assert config.deliver_policy == DeliverPolicy.ALL
    assert config.replay_policy == ReplayPolicy.INSTANT
    assert config.max_deliver == 5
    assert config.max_ack_pending == 100


async def test_push_consumer_config_properties() -> None:
    config = PushConsumerConfig(
        deliver_subject="test.deliver",
        name="test-push",
        description="push test",
        ack_policy=AckPolicy.EXPLICIT,
        deliver_policy=DeliverPolicy.NEW,
    )
    assert config.deliver_subject == "test.deliver"
    assert config.name == "test-push"
    assert config.description == "push test"
    assert config.ack_policy == AckPolicy.EXPLICIT
    assert config.deliver_policy == DeliverPolicy.NEW
