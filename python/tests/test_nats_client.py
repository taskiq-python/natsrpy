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
    async with nats.subscribe(subject=subj) as sub:
        await nats.publish(subj, payload)
        await nats.flush()
        message = await anext(sub)
    assert message.payload == payload


async def test_nats_drain(nats_url: str) -> None:
    client = Nats(addrs=[nats_url])
    await client.startup()
    await client.drain()


async def test_nats_startup_shutdown_cycle(nats_url: str) -> None:
    client = Nats(addrs=[nats_url])
    await client.startup()
    subj = uuid.uuid4().hex
    payload = b"cycle-test"
    async with client.subscribe(subject=subj) as sub:
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
    async with client2.subscribe(subject=subj) as sub:
        await client1.publish(subj, payload)
        message = await anext(sub)
    assert message.payload == payload

    await client1.shutdown()
    await client2.shutdown()


async def test_nats_publish_str_payload(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    payload_str = "hello-string"
    async with nats.subscribe(subject=subj) as sub:
        await nats.publish(subj, payload_str)
    message = await anext(sub)
    assert message.payload == payload_str.encode()


async def test_nats_publish_empty_payload(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    async with nats.subscribe(subject=subj) as sub:
        await nats.publish(subj, b"")
        message = await anext(sub)
    assert message.payload == b""


async def test_nats_publish_with_reply(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    reply_subj = uuid.uuid4().hex
    async with nats.subscribe(subject=subj) as sub:
        await nats.publish(subj, b"with-reply", reply=reply_subj)
        message = await anext(sub)
    assert message.payload == b"with-reply"
    assert message.reply == reply_subj


async def test_nats_connection_failure() -> None:
    nats = Nats(addrs=["localhost:19999"])
    with pytest.raises(Exception):
        await nats.startup()


async def test_nats_addr_property(nats_url: str) -> None:
    nats = Nats(addrs=[nats_url])
    assert nats.addr == [nats_url]


async def test_nats_addr_default() -> None:
    nats = Nats()
    assert nats.addr == ["nats://localhost:4222"]


async def test_nats_token_property() -> None:
    nats = Nats(token="secret-token")  # noqa: S106
    assert nats.token == "secret-token"  # noqa: S105


async def test_nats_token_default() -> None:
    nats = Nats()
    assert nats.token is None


async def test_nats_nkey_property() -> None:
    nats = Nats()
    assert nats.nkey is None


async def test_nats_user_and_pass_property() -> None:
    nats = Nats(user_and_pass=("user", "pass"))
    assert nats.user_and_pass == ("user", "pass")


async def test_nats_user_and_pass_default() -> None:
    nats = Nats()
    assert nats.user_and_pass is None


async def test_nats_custom_inbox_prefix_property() -> None:
    nats = Nats(custom_inbox_prefix="_custom")
    assert nats.custom_inbox_prefix == "_custom"


async def test_nats_custom_inbox_prefix_default() -> None:
    nats = Nats()
    assert nats.custom_inbox_prefix is None


async def test_nats_read_buffer_capacity_property() -> None:
    nats = Nats(read_buffer_capacity=1024)
    assert nats.read_buffer_capacity == 1024


async def test_nats_read_buffer_capacity_default() -> None:
    nats = Nats()
    assert nats.read_buffer_capacity == 65535


async def test_nats_sender_capacity_property() -> None:
    nats = Nats(sender_capacity=64)
    assert nats.sender_capacity == 64


async def test_nats_sender_capacity_default() -> None:
    nats = Nats()
    assert nats.sender_capacity == 128


async def test_nats_max_reconnects_property() -> None:
    nats = Nats(max_reconnects=5)
    assert nats.max_reconnects == 5


async def test_nats_max_reconnects_default() -> None:
    nats = Nats()
    assert nats.max_reconnects is None
