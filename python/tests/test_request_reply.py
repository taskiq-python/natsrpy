import asyncio
import uuid

from natsrpy import Message, Nats


async def test_request_sends_with_reply(nats: Nats) -> None:
    subj = uuid.uuid4().hex

    received_msgs: list[Message] = []

    async def responder() -> None:
        sub = await nats.subscribe(subject=subj)
        msg = await anext(sub)
        received_msgs.append(msg)
        if msg.reply:
            await nats.publish(msg.reply, b"reply-data")

    task = asyncio.create_task(responder())
    await asyncio.sleep(0.1)

    response = await nats.request(subj, b"request-payload")
    await task

    assert response.payload == b"reply-data"
    assert received_msgs
    assert received_msgs[0].payload == b"request-payload"
    assert received_msgs[0].reply is not None


async def test_request_with_headers(nats: Nats) -> None:
    subj = uuid.uuid4().hex

    received_msgs: list[Message] = []

    async def responder() -> None:
        sub = await nats.subscribe(subject=subj)
        msg = await anext(sub)
        received_msgs.append(msg)
        if msg.reply:
            await nats.publish(msg.reply, b"reply")

    task = asyncio.create_task(responder())
    await asyncio.sleep(0.1)

    resp = await nats.request(subj, b"data", headers={"x-custom": "value"})
    await task
    assert resp.payload == b"reply"
    assert received_msgs[0].headers == {"x-custom": "value"}


async def test_request_none_payload(nats: Nats) -> None:
    subj = uuid.uuid4().hex

    received_msgs: list[Message] = []

    async def responder() -> None:
        sub = await nats.subscribe(subject=subj)
        msg = await anext(sub)
        received_msgs.append(msg)
        if msg.reply:
            await nats.publish(msg.reply, b"reply")

    task = asyncio.create_task(responder())
    await asyncio.sleep(0.1)

    response = await nats.request(subj, b"")
    await task
    assert response.payload == b"reply"

    assert received_msgs[0].payload == b""
