import uuid

import pytest
from natsrpy import Nats


async def test_nats_default_constructor() -> None:
    nats = Nats()
    await nats.startup()
    await nats.shutdown()


async def test_nats_custom_addrs() -> None:
    nats = Nats(addrs=["localhost:4222"])
    await nats.startup()
    await nats.shutdown()


async def test_nats_flush(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    payload = b"flush-test"
    sub = await nats.subscribe(subject=subj)
    await nats.publish(subj, payload)
    await nats.flush()
    message = await anext(sub)
    assert message.payload == payload


async def test_nats_drain(nats_url: str) -> None:
    client = Nats(addrs=[nats_url])
    await client.startup()
    subj = uuid.uuid4().hex
    await client.subscribe(subject=subj)
    await client.drain()


async def test_nats_startup_shutdown_cycle(nats_url: str) -> None:
    client = Nats(addrs=[nats_url])
    await client.startup()
    subj = uuid.uuid4().hex
    payload = b"cycle-test"
    sub = await client.subscribe(subject=subj)
    await client.publish(subj, payload)
    message = await anext(sub)
    assert message.payload == payload
    await client.shutdown()


async def test_nats_multiple_connections(nats_url: str) -> None:
    client1 = Nats(addrs=[nats_url])
    client2 = Nats(addrs=[nats_url])
    await client1.startup()
    await client2.startup()

    subj = uuid.uuid4().hex
    payload = b"cross-client"
    sub = await client2.subscribe(subject=subj)
    await client1.publish(subj, payload)
    message = await anext(sub)
    assert message.payload == payload

    await client1.shutdown()
    await client2.shutdown()


async def test_nats_publish_str_payload(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    payload_str = "hello-string"
    sub = await nats.subscribe(subject=subj)
    await nats.publish(subj, payload_str)
    message = await anext(sub)
    assert message.payload == payload_str.encode()


async def test_nats_publish_empty_payload(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    sub = await nats.subscribe(subject=subj)
    await nats.publish(subj, b"")
    message = await anext(sub)
    assert message.payload == b""


async def test_nats_publish_with_reply(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    reply_subj = uuid.uuid4().hex
    sub = await nats.subscribe(subject=subj)
    await nats.publish(subj, b"with-reply", reply=reply_subj)
    message = await anext(sub)
    assert message.payload == b"with-reply"
    assert message.reply == reply_subj


async def test_nats_connection_failure() -> None:
    nats = Nats(addrs=["localhost:19999"])
    with pytest.raises(Exception):
        await nats.startup()
