import asyncio

from natsrpy import Nats
from natsrpy.js import PullConsumerConfig, PushConsumerConfig, StreamConfig


async def main() -> None:
    """Main function to run the example."""
    nats = Nats(["nats://localhost:4222"])
    await nats.startup()

    js = await nats.jetstream()

    stream = await js.streams.create_or_update(
        StreamConfig(
            name="stream-example",
            subjects=["stream.example.>"],
            description="Stream example",
        ),
    )

    # Push and pull consumers have different configurations.
    # If you supply PushConsumerConfig, you will get a push consumer,
    # and otherwise you will get a PullConsumer.
    #
    # They have different APIs.
    pull_consumer = await stream.consumers.create(
        PullConsumerConfig(
            name="example-pull",
            durable_name="example-pull",
        ),
    )
    push_consumer = await stream.consumers.create(
        PushConsumerConfig(
            name="example-push",
            deliver_subject="example-push",
            durable_name="example-push",
        ),
    )

    # We publish a single message
    await js.publish("stream.example.test", "message for stream")

    async with push_consumer.consume() as messages:
        async for push_message in messages:
            print(f"[FROM_PUSH] {push_message.payload!r}")  # noqa: T201
            break

    # Pull consumers have 2 different APIs.
    # 1. You can use fetch directly.
    # 2. Use async iterator API.

    # Here's how to call pull-consumer fetch method.
    # It returns a batch of messages.
    # However, please be careful, this method has worse opentelemetry
    # instrumentation. Because essentailly it's the same as just calling a function.
    # with no scope.
    for pull_message in await pull_consumer.fetch(max_messages=10):
        print(f"[FROM_PULL] {pull_message.payload!r}")  # noqa: T201
        await pull_message.ack()

    # This API is more prefered, because it has better
    # Opentelemetry instrumentation.
    async with pull_consumer.consume() as messages:
        async for message in messages:
            print(f"[FROM_PULL] {message.payload!r}")  # noqa: T201
            break

    # Cleanup
    await stream.consumers.delete(push_consumer.name)
    await stream.consumers.delete(pull_consumer.name)
    await js.streams.delete(stream.name)

    # Don't forget to call shutdown.
    await nats.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
