import uuid
from datetime import timedelta

from natsrpy.js import (
    JetStream,
    PullConsumer,
    PullConsumerConfig,
    PushConsumer,
    PushConsumerConfig,
    StreamConfig,
)


async def test_consumers_manager_delete(js: JetStream) -> None:
    stream_name = f"test-cmdel-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        consumer_name = f"consumer-{uuid.uuid4().hex[:8]}"
        await stream.consumers.create(PullConsumerConfig(name=consumer_name))
        result = await stream.consumers.delete(consumer_name)
        assert result is True
    finally:
        await js.streams.delete(stream_name)


async def test_consumers_manager_get_push(js: JetStream) -> None:
    stream_name = f"test-cmgp-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        deliver_subj = uuid.uuid4().hex
        consumer_name = f"push-{uuid.uuid4().hex[:8]}"
        await stream.consumers.create(
            PushConsumerConfig(deliver_subject=deliver_subj, name=consumer_name),
        )
        consumer = await stream.consumers.get_push(consumer_name)
        assert isinstance(consumer, PushConsumer)
        assert consumer.name == consumer_name
    finally:
        await js.streams.delete(stream_name)


async def test_consumers_manager_update_pull(js: JetStream) -> None:
    stream_name = f"test-cmup-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        consumer_name = f"consumer-{uuid.uuid4().hex[:8]}"
        cfg = PullConsumerConfig(name=consumer_name, description="original")
        await stream.consumers.create(cfg)
        cfg.description = "updated"
        updated = await stream.consumers.update(cfg)
        assert isinstance(updated, PullConsumer)
    finally:
        await js.streams.delete(stream_name)


async def test_consumers_manager_update_push(js: JetStream) -> None:
    stream_name = f"test-cmupp-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        deliver_subj = uuid.uuid4().hex
        consumer_name = f"push-{uuid.uuid4().hex[:8]}"
        cfg = PushConsumerConfig(
            deliver_subject=deliver_subj,
            name=consumer_name,
            description="original",
        )
        await stream.consumers.create(cfg)
        cfg.description = "updated"
        updated = await stream.consumers.update(cfg)
        assert isinstance(updated, PushConsumer)
    finally:
        await js.streams.delete(stream_name)


async def test_consumers_manager_pause_and_resume(js: JetStream) -> None:
    stream_name = f"test-cmpr-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        consumer_name = f"consumer-{uuid.uuid4().hex[:8]}"
        await stream.consumers.create(PullConsumerConfig(name=consumer_name))
        paused = await stream.consumers.pause(consumer_name, delay=60.0)
        assert isinstance(paused, bool)
        resumed = await stream.consumers.resume(consumer_name)
        assert isinstance(resumed, bool)
    finally:
        await js.streams.delete(stream_name)


async def test_consumers_manager_pause_timedelta(js: JetStream) -> None:
    stream_name = f"test-cmpd-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        consumer_name = f"consumer-{uuid.uuid4().hex[:8]}"
        await stream.consumers.create(PullConsumerConfig(name=consumer_name))
        paused = await stream.consumers.pause(
            consumer_name,
            delay=timedelta(seconds=60),
        )
        assert isinstance(paused, bool)
    finally:
        await js.streams.delete(stream_name)
