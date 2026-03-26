import asyncio

from natsrpy import Message, Nats


async def main() -> None:
    """Main function to run the example."""
    nats = Nats(["nats://localhost:4222"])
    await nats.startup()

    cb_lock = asyncio.Event()

    async def callback(message: Message) -> None:
        print(f"[FROM_CALLBACK] {message.payload}")  # noqa: T201
        cb_lock.set()

    # When subscribing you can set callback.
    # In that case CallbackSubscription is returned.
    # This type of subscription cannot be iterated.
    cb_sub = await nats.subscribe("cb-subj", callback=callback)

    # When callback is not set, you get a subscription
    # that should be used along with `async for`
    # loop, or alternatively you can call
    # `await iter_sub.next()` to get a single message.
    iter_sub = await nats.subscribe("iter-subj")

    # Subscriptions with queue argument create
    # subscription with a queue group to distribute
    # messages along all subscribers.
    queue_sub = await nats.subscribe("queue-subj", queue="example-queue")

    await nats.publish("cb-subj", "message for callback")
    await nats.publish("iter-subj", "message for iterator")
    await nats.publish("queue-subj", "message for queue sub")

    # We can unsubscribe after a particular amount of messages.
    await iter_sub.unsubscribe(limit=1)
    await cb_sub.unsubscribe(limit=1)
    await queue_sub.unsubscribe(limit=1)

    async for message in iter_sub:
        print(f"[FROM_ITERATOR] {message.payload}")  # noqa: T201

    async for message in queue_sub:
        print(f"[FROM_QUEUED] {message.payload}")  # noqa: T201

    # Making sure that the message in callback is received.
    await cb_lock.wait()

    # Don't forget to call shutdown.
    await nats.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
