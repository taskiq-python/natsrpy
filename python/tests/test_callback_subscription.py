import asyncio
import uuid

from natsrpy import CallbackSubscription, Message, Nats


async def test_callback_unsubscribe(nats: Nats) -> None:
    subj = uuid.uuid4().hex

    async def callback(_: Message) -> None: ...

    async with nats.subscribe(subject=subj, callback=callback) as sub:
        assert isinstance(sub, CallbackSubscription)
        await sub.unsubscribe()


async def test_callback_unsubscribe_with_limit(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    received: list[bytes] = []
    event = asyncio.Event()

    async def callback(msg: Message) -> None:
        received.append(msg.payload)
        if len(received) >= 2:
            event.set()

    async with nats.subscribe(subject=subj, callback=callback) as sub:
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

    async def callback(_: object) -> None: ...

    async with client.subscribe(subject=subj, callback=callback) as sub:
        assert isinstance(sub, CallbackSubscription)
        await sub.drain()
    await client.shutdown()


async def test_callback_wait_method(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    received: list[bytes] = []
    limit = 10

    async def callback(msg: Message) -> None:
        await asyncio.sleep(0.1)
        received.append(msg.payload)

    async with nats.subscribe(subject=subj, callback=callback) as sub:
        assert isinstance(sub, CallbackSubscription)
        await sub.unsubscribe(limit=limit)
        for _ in range(limit):
            await nats.publish(subj, b"msg-1")
        await asyncio.wait_for(sub.wait(), timeout=5.0)
        assert len(received) == limit
