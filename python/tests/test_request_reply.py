import asyncio
import uuid

from natsrpy import Nats


async def test_request_sends_with_reply(nats: Nats) -> None:
    subj = uuid.uuid4().hex

    received_payload: list[bytes] = []
    received_reply: list[str | None] = []

    async def responder() -> None:
        sub = await nats.subscribe(subject=subj)
        msg = await anext(sub)
        received_payload.append(msg.payload)
        received_reply.append(msg.reply)
        if msg.reply:
            await nats.publish(msg.reply, b"reply-data")

    task = asyncio.create_task(responder())
    await asyncio.sleep(0.1)

    # request() sends a message and waits for a reply (though the response
    # is not returned by the current implementation)
    await nats.request(subj, b"request-payload")
    await task

    assert received_payload == [b"request-payload"]
    # request() should set a reply subject automatically
    assert received_reply[0] is not None


async def test_request_with_headers(nats: Nats) -> None:
    subj = uuid.uuid4().hex

    received_headers: list[dict[str, str]] = []

    async def responder() -> None:
        sub = await nats.subscribe(subject=subj)
        msg = await anext(sub)
        received_headers.append(msg.headers)
        if msg.reply:
            await nats.publish(msg.reply, b"reply")

    task = asyncio.create_task(responder())
    await asyncio.sleep(0.1)

    await nats.request(subj, b"data", headers={"x-custom": "value"})
    await task

    assert received_headers[0] == {"x-custom": "value"}


async def test_request_none_payload(nats: Nats) -> None:
    subj = uuid.uuid4().hex

    received_payload: list[bytes] = []

    async def responder() -> None:
        sub = await nats.subscribe(subject=subj)
        msg = await anext(sub)
        received_payload.append(msg.payload)
        if msg.reply:
            await nats.publish(msg.reply, b"reply")

    task = asyncio.create_task(responder())
    await asyncio.sleep(0.1)

    await nats.request(subj, b"")
    await task

    assert received_payload[0] == b""
