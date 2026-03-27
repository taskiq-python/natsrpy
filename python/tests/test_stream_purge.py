import uuid

from natsrpy.js import JetStream, StreamConfig


async def test_stream_purge_with_sequence(js: JetStream) -> None:
    name = f"test-purgeseq-{uuid.uuid4().hex[:8]}"
    subj = f"{name}.data"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"msg-1", wait=True)
        await js.publish(subj, b"msg-2", wait=True)
        await js.publish(subj, b"msg-3", wait=True)
        purged = await stream.purge(sequence=2)
        assert purged >= 1
        info = await stream.get_info()
        assert info.state.messages < 3
    finally:
        await js.streams.delete(name)


async def test_stream_purge_with_keep(js: JetStream) -> None:
    name = f"test-purgekeep-{uuid.uuid4().hex[:8]}"
    subj = f"{name}.data"
    config = StreamConfig(name=name, subjects=[f"{name}.>"])
    stream = await js.streams.create(config)
    try:
        await js.publish(subj, b"msg-1", wait=True)
        await js.publish(subj, b"msg-2", wait=True)
        await js.publish(subj, b"msg-3", wait=True)
        await js.publish(subj, b"msg-4", wait=True)
        await js.publish(subj, b"msg-5", wait=True)
        purged = await stream.purge(keep=2)
        assert purged == 3
        info = await stream.get_info()
        assert info.state.messages == 2
    finally:
        await js.streams.delete(name)
