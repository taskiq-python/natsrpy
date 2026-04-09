import asyncio
import uuid

import pytest
from natsrpy import CallbackSubscription, IteratorSubscription, Message, Nats


async def test_subscribe_returns_iterator(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    async with nats.subscribe(subject=subj) as sub:
        assert isinstance(sub, IteratorSubscription)


async def test_subscribe_with_callback(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    received: list[bytes] = []
    event = asyncio.Event()

    async def callback(msg: Message) -> None:
        received.append(msg.payload)
        event.set()

    async with nats.subscribe(subject=subj, callback=callback) as sub:
        assert isinstance(sub, CallbackSubscription)
        await nats.publish(subj, b"callback-test")
        await asyncio.wait_for(event.wait(), timeout=5.0)
    assert received == [b"callback-test"]


async def test_iterator_next_with_timeout(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    async with nats.subscribe(subject=subj) as sub:
        await nats.publish(subj, b"timeout-test")
        message = await asyncio.wait_for(anext(sub), timeout=5.0)
    assert message.payload == b"timeout-test"


async def test_iterator_aiter_protocol(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    async with nats.subscribe(subject=subj) as sub:
        payloads = [f"msg-{i}".encode() for i in range(3)]
        for p in payloads:
            await nats.publish(subj, p)

        received = []
        async for msg in sub:
            received.append(msg.payload)
            if len(received) == 3:
                break
    assert received == payloads


async def test_iterator_unsubscribe(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    async with nats.subscribe(subject=subj) as sub:
        await sub.unsubscribe()


async def test_iterator_unsubscribe_with_limit(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    async with nats.subscribe(subject=subj) as sub:
        await sub.unsubscribe(limit=2)
        await nats.publish(subj, b"msg-1")
        await nats.publish(subj, b"msg-2")
        msg1 = await asyncio.wait_for(anext(sub), timeout=5.0)
        msg2 = await asyncio.wait_for(anext(sub), timeout=5.0)
        assert msg1.payload == b"msg-1"
        assert msg2.payload == b"msg-2"
        with pytest.raises(StopAsyncIteration):
            await asyncio.wait_for(anext(sub), timeout=5.0)


async def test_iterator_drain(nats_url: str) -> None:
    client = Nats(addrs=[nats_url])
    await client.startup()
    subj = uuid.uuid4().hex
    async with client.subscribe(subject=subj) as sub:
        await sub.drain()
    await client.shutdown()


async def test_callback_receives_message(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    event = asyncio.Event()

    async def callback(_: Message) -> None:
        event.set()

    async with nats.subscribe(subject=subj, callback=callback) as sub:
        assert isinstance(sub, CallbackSubscription)
        await nats.publish(subj, b"trigger")
        await asyncio.wait_for(event.wait(), timeout=5.0)


async def test_multiple_subscribers(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    async with (
        nats.subscribe(subject=subj) as sub1,
        nats.subscribe(subject=subj) as sub2,
    ):
        await nats.publish(subj, b"multi-sub")
        msg1 = await anext(sub1)
        msg2 = await anext(sub2)
        assert msg1.payload == b"multi-sub"
        assert msg2.payload == b"multi-sub"


async def test_wildcard_subscription(nats: Nats) -> None:
    prefix = uuid.uuid4().hex
    async with nats.subscribe(subject=f"{prefix}.*") as sub:
        await nats.publish(f"{prefix}.one", b"wildcard-1")
        await nats.publish(f"{prefix}.two", b"wildcard-2")
        msg1 = await anext(sub)
        msg2 = await anext(sub)
        assert msg1.payload == b"wildcard-1"
        assert msg2.payload == b"wildcard-2"


async def test_fullwild_subscription(nats: Nats) -> None:
    prefix = uuid.uuid4().hex
    async with nats.subscribe(subject=f"{prefix}.>") as sub:
        await nats.publish(f"{prefix}.a.b.c", b"full-wild")
        msg = await anext(sub)
        assert msg.payload == b"full-wild"
        assert msg.subject == f"{prefix}.a.b.c"


async def test_subscription_ctx_manager_detatch(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    ctx = nats.subscribe(subject=subj)
    sub = await ctx.detatch()
    assert isinstance(sub, IteratorSubscription)
    await nats.publish(subj, b"detatch-test")
    msg = await asyncio.wait_for(anext(sub), timeout=5.0)
    assert msg.payload == b"detatch-test"
    await sub.unsubscribe()
