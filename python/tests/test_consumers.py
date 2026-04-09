import asyncio
import uuid

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


async def test_pull_consumer_create(js: JetStream) -> None:
    stream_name = f"test-pcreate-{uuid.uuid4()}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4()}",
        )
        consumer = await stream.consumers.create(consumer_config)
        assert isinstance(consumer, PullConsumer)
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_fetch_with_ack(js: JetStream) -> None:
    stream_name = f"test-pack-{uuid.uuid4()}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"ack-msg", wait=True)

        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4()}",
            ack_policy=AckPolicy.EXPLICIT,
        )
        consumer = await stream.consumers.create(consumer_config)
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        await messages[0].ack()
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_nack(js: JetStream) -> None:
    stream_name = f"test-pnack-{uuid.uuid4()}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"nack-msg", wait=True)

        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4()}",
            ack_policy=AckPolicy.EXPLICIT,
        )
        consumer = await stream.consumers.create(consumer_config)
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        await messages[0].nack()
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_term(js: JetStream) -> None:
    stream_name = f"test-pterm-{uuid.uuid4()}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"term-msg", wait=True)

        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4()}",
            ack_policy=AckPolicy.EXPLICIT,
        )
        consumer = await stream.consumers.create(consumer_config)
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        await messages[0].term()
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_progress(js: JetStream) -> None:
    stream_name = f"test-pprog-{uuid.uuid4()}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"progress-msg", wait=True)

        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4()}",
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
    stream_name = f"test-pmsgprop-{uuid.uuid4()}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"prop-msg", wait=True)

        consumer_name = f"consumer-{uuid.uuid4()}"
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
    stream_name = f"test-pfilter-{uuid.uuid4()}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(f"{stream_name}.a", b"msg-a", wait=True)
        await js.publish(f"{stream_name}.b", b"msg-b", wait=True)

        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4()}",
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
    stream_name = f"test-pdeliver-{uuid.uuid4()}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"old-msg", wait=True)
        await js.publish(subj, b"new-msg", wait=True)

        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4()}",
            deliver_policy=DeliverPolicy.LAST,
        )
        consumer = await stream.consumers.create(consumer_config)
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        assert messages[0].payload == b"new-msg"
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_replay_policy(js: JetStream) -> None:
    stream_name = f"test-preplay-{uuid.uuid4()}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        consumer_config = PullConsumerConfig(
            name=f"consumer-{uuid.uuid4()}",
            replay_policy=ReplayPolicy.INSTANT,
        )
        consumer = await stream.consumers.create(consumer_config)
        assert isinstance(consumer, PullConsumer)
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_durable(js: JetStream) -> None:
    stream_name = f"test-pdurable-{uuid.uuid4()}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        durable_name = f"durable-{uuid.uuid4()}"
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
    stream_name = f"test-pushcreate-{uuid.uuid4()}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        deliver_subj = uuid.uuid4().hex
        consumer_config = PushConsumerConfig(
            deliver_subject=deliver_subj,
            name=f"consumer-{uuid.uuid4()}",
        )
        consumer = await stream.consumers.create(consumer_config)
        assert isinstance(consumer, PushConsumer)
    finally:
        await js.streams.delete(stream_name)


async def test_pull_consumer_messages(js: JetStream) -> None:
    stream_name = f"test-pushmsg-{uuid.uuid4()}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    messages = [uuid.uuid4().hex.encode(), uuid.uuid4().hex.encode()]
    stream = await js.streams.create(config)
    try:
        for message in messages:
            await js.publish(subj, message, wait=True)
        consumer_config = PullConsumerConfig(name=f"consumer-{uuid.uuid4()}")
        consumer = await stream.consumers.create(consumer_config)
        msgs_iter = await consumer.fetch(timeout=0.5)
        for nats_msg, payload in zip(msgs_iter, messages, strict=True):
            assert nats_msg.payload == payload
    finally:
        await js.streams.delete(stream_name)


async def test_push_consumer_messages(js: JetStream) -> None:
    stream_name = f"test-pushmsg-{uuid.uuid4()}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    messages = [uuid.uuid4().hex.encode(), uuid.uuid4().hex.encode()]
    stream = await js.streams.create(config)
    try:
        for message in messages:
            await js.publish(subj, message, wait=True)

        deliver_subj = uuid.uuid4().hex
        consumer_config = PushConsumerConfig(
            deliver_subject=deliver_subj,
            name=f"consumer-{uuid.uuid4()}",
        )
        consumer = await stream.consumers.create(consumer_config)
        async with consumer.consume() as consumer_messages:
            for message in messages:
                nats_msg = await asyncio.wait_for(anext(consumer_messages), timeout=0.5)
                assert message == nats_msg.payload

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


async def test_pull_consumer_consume_context_manager(js: JetStream) -> None:
    stream_name = f"test-pullctx-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"consume-msg", wait=True)
        consumer = await stream.consumers.create(
            PullConsumerConfig(name=f"consumer-{uuid.uuid4().hex[:8]}"),
        )
        async with consumer.consume() as fetcher:
            msg = await anext(fetcher)
            assert msg.payload == b"consume-msg"
            await msg.ack()
    finally:
        await js.streams.delete(stream_name)


async def test_push_consumer_consume_context_manager(js: JetStream) -> None:
    stream_name = f"test-pushctx-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"push-consume-msg", wait=True)
        deliver_subj = uuid.uuid4().hex
        consumer = await stream.consumers.create(
            PushConsumerConfig(
                deliver_subject=deliver_subj,
                name=f"push-{uuid.uuid4().hex[:8]}",
            ),
        )
        async with consumer.consume() as msgs:
            msg = await anext(msgs)
            assert msg.payload == b"push-consume-msg"
            await msg.ack()
    finally:
        await js.streams.delete(stream_name)
