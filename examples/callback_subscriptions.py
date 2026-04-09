import asyncio

from natsrpy import Message, Nats


async def main() -> None:
    """Main function to run the example."""
    nats = Nats(["nats://localhost:4222"])
    await nats.startup()

    async def callback(message: Message) -> None:
        print(f"[FROM_CALLBACK] {message.payload!r}")  # noqa: T201

    async with nats.subscribe("cb-subj", callback=callback) as sub:
        # Lets you unsubscribe after `n` messages.
        await sub.unsubscribe(limit=1)
        await nats.publish("cb-subj", "context-based")
        # Waits for subscription to be drained.
        # Reach limit in our case.
        await sub.wait()

    # For callback subscriptions you can use detatch method.
    #
    # This method does the same as __enter__, however since
    # it's a callback-based subscription, context managers
    # are ususally not needed.
    #
    # But please save the reference somewhere, since python garbage
    # collector might collect your detatched subscription and
    # stop receiving any new messages.
    cb_sub = await nats.subscribe("cb-subj", callback=callback).detatch()
    await cb_sub.unsubscribe(limit=1)

    nats.publish("cb-subj", "detached version")

    # Waiting for subscriber to read all the messages.
    await cb_sub.wait()

    # Don't forget to call shutdown.
    await nats.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
