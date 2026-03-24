import asyncio
import logging
from datetime import timedelta

from natsrpy import Nats, Message
from natsrpy.js import PullConsumerConfig, StreamConfig

logging.basicConfig(level=logging.DEBUG)


async def do_things(nats: Nats) -> None:
    """Do things."""
    js = await nats.jetstream()
    stream = await js.streams.create_or_update(
        StreamConfig(
            subjects=["test.one", "test.two"],
            name="test-stream",
        ),
    )
    await js.publish("test.one", b"Hello lib!")

    consumer = await stream.consumers.create(
        PullConsumerConfig(
            name="test-cons",
            durable_name="test-cons",
        ),
    )
    while True:
        for message in await consumer.fetch():
            print(
                message.subject,
                message.reply,
                message.payload,
                message.headers,
                message.domain,
                message.acc_hash,
                message.stream,
                message.consumer,
                message.stream_sequence,
                message.consumer_sequence,
                message.delivered,
                message.pending,
                message.published,
                message.token,
                sep="||",
            )
            await message.ack()

    await asyncio.Future()


async def main() -> None:
    """We do logic here."""
    nats = Nats(
        addrs=["nats://localhost:4222"],
        connection_timeout=timedelta(seconds=1),
        request_timeout=timedelta(seconds=3),
    )
    await nats.startup()

    try:
        await do_things(nats)
    finally:
        await nats.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
