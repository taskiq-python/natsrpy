import asyncio

from natsrpy import Nats


async def main() -> None:
    """Main function to run the example."""
    nats = Nats(["nats://localhost:4222"])
    await nats.startup()

    # Here we initiate subscription.
    # We do it before sending messages,
    # in order to catch them once we will start reading.
    subscription = await nats.subscribe("hello")

    # Publish accepts str | bytes | bytearray | memoryview
    await nats.publish("hello", "str world")
    await nats.publish("hello", b"bytes world")
    await nats.publish("hello", bytearray(b"bytearray world"))
    await nats.publish("hello", "headers", headers={"one": "two"})
    await nats.publish("hello", "headers", headers={"one": ["two", "three"]})

    # Calling this method will unsubscribe us,
    # after `n` delivered messages.
    # or immediately if `n` is not provided.
    subscription.unsubscribe(limit=5)
    async for message in subscription:
        print(message)  # noqa: T201

    # Don't forget to call shutdown.
    await nats.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
