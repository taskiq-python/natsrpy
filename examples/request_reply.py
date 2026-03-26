import asyncio

from natsrpy import Message, Nats


async def main() -> None:
    """Main function to run the example."""
    nats = Nats(["nats://localhost:4222"])
    await nats.startup()
    subj = "request-reply"

    # Here we create responder, that will be
    # answering to our requests.
    async def responder(message: Message) -> None:
        print(f"[REQUEST]: {message.payload}, headers={message.headers}")  # noqa: T201
        if message.reply:
            await nats.publish(
                message.reply,
                f"reply to {message.payload}",
                headers=message.headers,
            )

    # Start responder using callback-based subsciption.
    sub = await nats.subscribe(subj, callback=responder)
    # Send 3 concurrent requests.
    responses = await asyncio.gather(
        nats.request(subj, "request1"),
        nats.request(subj, "request2", headers={"header": "value"}),
        nats.request(subj, "request3", inbox="test-inbox"),
    )
    # Disconnect resonder.
    await sub.drain()

    # Iterate over replies.
    for resp in responses:
        print(f"[RESPONSE]: {resp}")  # noqa: T201

    await nats.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
