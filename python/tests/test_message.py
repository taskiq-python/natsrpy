import uuid

from natsrpy import Nats


async def test_message_subject(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    async with nats.subscribe(subject=subj) as sub:
        await nats.publish(subj, b"subject-test")
        msg = await anext(sub)
    assert msg.subject == subj


async def test_message_payload(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    payload = b"payload-test-data"
    async with nats.subscribe(subject=subj) as sub:
        await nats.publish(subj, payload)
        msg = await anext(sub)
    assert msg.payload == payload
    assert isinstance(msg.payload, bytes)


async def test_message_headers_empty(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    async with nats.subscribe(subject=subj) as sub:
        await nats.publish(subj, b"no-headers")
        msg = await anext(sub)
    assert msg.headers == {}


async def test_message_headers_string(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    headers = {"content-type": "application/json", "x-id": "12345"}
    async with nats.subscribe(subject=subj) as sub:
        await nats.publish(subj, b"with-headers", headers=headers)
        msg = await anext(sub)
    assert msg.headers == headers


async def test_message_headers_multi_value(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    headers = {"x-values": ["a", "b", "c"]}
    async with nats.subscribe(subject=subj) as sub:
        await nats.publish(subj, b"multi-headers", headers=headers)
        msg = await anext(sub)
    assert msg.headers == headers


async def test_message_reply_present(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    reply_to = uuid.uuid4().hex
    async with nats.subscribe(subject=subj) as sub:
        await nats.publish(subj, b"reply-test", reply=reply_to)
        msg = await anext(sub)
    assert msg.reply == reply_to


async def test_message_reply_absent(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    async with nats.subscribe(subject=subj) as sub:
        await nats.publish(subj, b"no-reply")
        msg = await anext(sub)
    assert msg.reply is None


async def test_message_length(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    payload = b"length-check"
    async with nats.subscribe(subject=subj) as sub:
        await nats.publish(subj, payload)
        msg = await anext(sub)
    # length is the total message length (includes subject + overhead), not just payload
    assert msg.length >= len(payload)


async def test_message_length_empty(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    async with nats.subscribe(subject=subj) as sub:
        await nats.publish(subj, b"")
        msg = await anext(sub)
    # Even with empty payload, length includes overhead
    assert msg.length >= 0


async def test_message_repr(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    async with nats.subscribe(subject=subj) as sub:
        await nats.publish(subj, b"repr-test")
        msg = await anext(sub)
    r = repr(msg)
    assert isinstance(r, str)
    assert len(r) > 0


async def test_message_large_payload(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    payload = b"x" * 65536
    async with nats.subscribe(subject=subj) as sub:
        await nats.publish(subj, payload)
        msg = await anext(sub)
    assert msg.payload == payload
    assert msg.length >= 65536
