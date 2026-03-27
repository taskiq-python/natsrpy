import uuid

from natsrpy.js import (
    AckPolicy,
    JetStream,
    PullConsumerConfig,
    StreamConfig,
)


async def test_message_ack_double(js: JetStream) -> None:
    stream_name = f"test-ackd-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"ack-double", wait=True)
        consumer = await stream.consumers.create(
            PullConsumerConfig(
                name=f"consumer-{uuid.uuid4().hex[:8]}",
                ack_policy=AckPolicy.EXPLICIT,
            ),
        )
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        await messages[0].ack(double=True)
    finally:
        await js.streams.delete(stream_name)


async def test_message_nack_with_delay(js: JetStream) -> None:
    stream_name = f"test-nackd-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"nack-delay", wait=True)
        consumer = await stream.consumers.create(
            PullConsumerConfig(
                name=f"consumer-{uuid.uuid4().hex[:8]}",
                ack_policy=AckPolicy.EXPLICIT,
            ),
        )
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        await messages[0].nack(delay=2.0)
    finally:
        await js.streams.delete(stream_name)


async def test_message_nack_double(js: JetStream) -> None:
    stream_name = f"test-nackdb-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"nack-double", wait=True)
        consumer = await stream.consumers.create(
            PullConsumerConfig(
                name=f"consumer-{uuid.uuid4().hex[:8]}",
                ack_policy=AckPolicy.EXPLICIT,
            ),
        )
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        await messages[0].nack(double=True)
    finally:
        await js.streams.delete(stream_name)


async def test_message_next_ack(js: JetStream) -> None:
    stream_name = f"test-nextack-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"next-ack", wait=True)
        consumer = await stream.consumers.create(
            PullConsumerConfig(
                name=f"consumer-{uuid.uuid4().hex[:8]}",
                ack_policy=AckPolicy.EXPLICIT,
            ),
        )
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        await messages[0].next()
    finally:
        await js.streams.delete(stream_name)


async def test_message_term_double(js: JetStream) -> None:
    stream_name = f"test-termd-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"term-double", wait=True)
        consumer = await stream.consumers.create(
            PullConsumerConfig(
                name=f"consumer-{uuid.uuid4().hex[:8]}",
                ack_policy=AckPolicy.EXPLICIT,
            ),
        )
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        await messages[0].term(double=True)
    finally:
        await js.streams.delete(stream_name)


async def test_message_progress_double(js: JetStream) -> None:
    stream_name = f"test-progd-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"progress-double", wait=True)
        consumer = await stream.consumers.create(
            PullConsumerConfig(
                name=f"consumer-{uuid.uuid4().hex[:8]}",
                ack_policy=AckPolicy.EXPLICIT,
            ),
        )
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        await messages[0].progress(double=True)
        await messages[0].ack()
    finally:
        await js.streams.delete(stream_name)


async def test_message_domain_and_acc_hash(js: JetStream) -> None:
    stream_name = f"test-domhash-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"domain-test", wait=True)
        consumer = await stream.consumers.create(
            PullConsumerConfig(name=f"consumer-{uuid.uuid4().hex[:8]}"),
        )
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        msg = messages[0]
        # domain may be None for a non-domain jetstream
        assert msg.domain is None or isinstance(msg.domain, str)
        assert msg.acc_hash is None or isinstance(msg.acc_hash, str)
        assert msg.token is None or isinstance(msg.token, str)
        assert msg.reply is None or isinstance(msg.reply, str)
    finally:
        await js.streams.delete(stream_name)


async def test_message_headers_empty(js: JetStream) -> None:
    stream_name = f"test-msghdr-{uuid.uuid4().hex[:8]}"
    subj = f"{stream_name}.data"
    config = StreamConfig(name=stream_name, subjects=[f"{stream_name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"no-headers", wait=True)
        consumer = await stream.consumers.create(
            PullConsumerConfig(name=f"consumer-{uuid.uuid4().hex[:8]}"),
        )
        messages = await consumer.fetch(max_messages=1, timeout=5.0)
        assert len(messages) == 1
        assert isinstance(messages[0].headers, dict)
    finally:
        await js.streams.delete(stream_name)
