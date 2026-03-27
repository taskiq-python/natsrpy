import asyncio
import uuid

from natsrpy import CallbackSubscription, Nats


async def test_callback_unsubscribe(nats: Nats) -> None:
    subj = uuid.uuid4().hex

    async def callback(msg: object) -> None:
        pass

    sub = await nats.subscribe(subject=subj, callback=callback)
    assert isinstance(sub, CallbackSubscription)
    await sub.unsubscribe()


async def test_callback_unsubscribe_with_limit(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    received: list[bytes] = []
    event = asyncio.Event()

    async def callback(msg: object) -> None:
        received.append(msg.payload)  # type: ignore[attr-defined]
        if len(received) >= 2:
            event.set()

    sub = await nats.subscribe(subject=subj, callback=callback)
    assert isinstance(sub, CallbackSubscription)
    await sub.unsubscribe(limit=2)
    await nats.publish(subj, b"msg-1")
    await nats.publish(subj, b"msg-2")
    await asyncio.wait_for(event.wait(), timeout=5.0)
    assert set(received) == {b"msg-1", b"msg-2"}


async def test_callback_drain(nats_url: str) -> None:
    client = Nats(addrs=[nats_url])
    await client.startup()
    subj = uuid.uuid4().hex

    async def callback(msg: object) -> None:
        pass

    sub = await client.subscribe(subject=subj, callback=callback)
    assert isinstance(sub, CallbackSubscription)
    await sub.drain()
    await client.shutdown()
