import uuid

from natsrpy.js import (
    JetStream,
    PullConsumer,
    PullConsumerConfig,
    PushConsumer,
    PushConsumerConfig,
    StreamConfig,
)


async def test_stream_direct_get_next_for_subject(js: JetStream) -> None:
    name = f"test-dgnfs-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"], allow_direct=True)
    stream = await js.streams.create(config)
    try:
        await js.publish(f"{name}.a", b"msg-a-1", wait=True)
        await js.publish(f"{name}.a", b"msg-a-2", wait=True)
        await js.publish(f"{name}.b", b"msg-b-1", wait=True)
        msg = await stream.direct_get_next_for_subject(f"{name}.a")
        assert msg.payload == b"msg-a-1"
        assert msg.subject == f"{name}.a"
    finally:
        await js.streams.delete(name)


async def test_stream_direct_get_next_for_subject_with_sequence(
    js: JetStream,
) -> None:
    name = f"test-dgnfss-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"], allow_direct=True)
    stream = await js.streams.create(config)
    try:
        await js.publish(f"{name}.a", b"msg-a-1", wait=True)
        await js.publish(f"{name}.a", b"msg-a-2", wait=True)
        await js.publish(f"{name}.b", b"msg-b-1", wait=True)
        msg = await stream.direct_get_next_for_subject(f"{name}.a", sequence=2)
        assert msg.payload == b"msg-a-2"
    finally:
        await js.streams.delete(name)


async def test_stream_direct_get_first_for_subject(js: JetStream) -> None:
    name = f"test-dgffs-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"], allow_direct=True)
    stream = await js.streams.create(config)
    try:
        await js.publish(f"{name}.a", b"first-msg", wait=True)
        await js.publish(f"{name}.a", b"second-msg", wait=True)
        msg = await stream.direct_get_first_for_subject(f"{name}.a")
        assert msg.payload == b"first-msg"
        assert msg.subject == f"{name}.a"
        assert msg.sequence == 1
    finally:
        await js.streams.delete(name)


async def test_stream_direct_get_last_for_subject(js: JetStream) -> None:
    name = f"test-dglfs-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"], allow_direct=True)
    stream = await js.streams.create(config)
    try:
        await js.publish(f"{name}.a", b"first-msg", wait=True)
        await js.publish(f"{name}.a", b"last-msg", wait=True)
        msg = await stream.direct_get_last_for_subject(f"{name}.a")
        assert msg.payload == b"last-msg"
        assert msg.subject == f"{name}.a"
        assert msg.sequence == 2
    finally:
        await js.streams.delete(name)


async def test_stream_delete_message(js: JetStream) -> None:
    name = f"test-delmsg-{uuid.uuid4().hex[:8]}"
    subj = f"{name}.data"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"msg-1", wait=True)
        await js.publish(subj, b"msg-2", wait=True)
        await js.publish(subj, b"msg-3", wait=True)
        info = await stream.get_info()
        assert info.state.messages == 3

        await stream.delete_message(sequence=2)

        info = await stream.get_info()
        assert info.state.messages == 2
    finally:
        await js.streams.delete(name)


async def test_consumers_list(js: JetStream) -> None:
    name = f"test-clist-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    stream = await js.streams.create(config)
    try:
        consumer_name1 = f"consumer-{uuid.uuid4().hex[:8]}"
        consumer_name2 = f"consumer-{uuid.uuid4().hex[:8]}"
        await stream.consumers.create(PullConsumerConfig(name=consumer_name1))
        await stream.consumers.create(PullConsumerConfig(name=consumer_name2))

        consumers_iter = await stream.consumers.list()
        found = []
        async for consumer in consumers_iter:
            assert isinstance(consumer, (PullConsumer, PushConsumer))
            found.append(consumer)
        assert len(found) == 2
    finally:
        await js.streams.delete(name)


async def test_consumers_list_returns_correct_types(js: JetStream) -> None:
    name = f"test-cltype-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    stream = await js.streams.create(config)
    try:
        pull_name = f"pull-{uuid.uuid4().hex[:8]}"
        push_name = f"push-{uuid.uuid4().hex[:8]}"
        await stream.consumers.create(PullConsumerConfig(name=pull_name))
        deliver_subj = uuid.uuid4().hex
        await stream.consumers.create(
            PushConsumerConfig(deliver_subject=deliver_subj, name=push_name),
        )

        consumers_iter = await stream.consumers.list()
        types_found: dict[str, type] = {}
        async for consumer in consumers_iter:
            if isinstance(consumer, PullConsumer):
                types_found["pull"] = type(consumer)
            elif isinstance(consumer, PushConsumer):
                types_found["push"] = type(consumer)
        assert types_found.get("pull") is PullConsumer
        assert types_found.get("push") is PushConsumer
    finally:
        await js.streams.delete(name)


async def test_consumers_list_names(js: JetStream) -> None:
    name = f"test-clnames-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    stream = await js.streams.create(config)
    try:
        consumer_name1 = f"consumer-{uuid.uuid4().hex[:8]}"
        consumer_name2 = f"consumer-{uuid.uuid4().hex[:8]}"
        await stream.consumers.create(PullConsumerConfig(name=consumer_name1))
        await stream.consumers.create(PullConsumerConfig(name=consumer_name2))

        names_iter = await stream.consumers.list_names()
        found_names: list[str] = []
        async for cname in names_iter:
            assert isinstance(cname, str)
            found_names.append(cname)
        assert sorted(found_names) == sorted([consumer_name1, consumer_name2])
    finally:
        await js.streams.delete(name)


async def test_consumers_list_empty(js: JetStream) -> None:
    name = f"test-clempty-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    stream = await js.streams.create(config)
    try:
        consumers_iter = await stream.consumers.list()
        found = []
        async for consumer in consumers_iter:
            found.append(consumer)
        assert len(found) == 0
    finally:
        await js.streams.delete(name)


async def test_consumers_list_names_empty(js: JetStream) -> None:
    name = f"test-clnempty-{uuid.uuid4().hex[:8]}"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    stream = await js.streams.create(config)
    try:
        names_iter = await stream.consumers.list_names()
        found_names: list[str] = []
        async for cname in names_iter:
            found_names.append(cname)
        assert len(found_names) == 0
    finally:
        await js.streams.delete(name)
