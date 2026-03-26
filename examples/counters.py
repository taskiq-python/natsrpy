import asyncio

from natsrpy import Nats
from natsrpy.js import CountersConfig


async def main() -> None:
    """Main function to run the example."""
    nats = Nats(["nats://localhost:4222"])
    await nats.startup()

    js = await nats.jetstream()
    # Counters store is basically a stream,
    # but each subject is considered as a counter.
    # You can read more about how it works here:
    # https://github.com/nats-io/nats-architecture-and-design/blob/main/adr/ADR-49.md
    counters = await js.counters.create_or_update(
        CountersConfig(
            name="counters",
            subjects=["counters.>"],
        ),
    )

    # We have a nice interface for counters.
    # Please note, that ADD accepts
    # positive and NEGATIVE values.
    # I'd rename this method, but this API is
    # defined in ADR-49, so we won't change this.
    #
    # Each add\incr\decr returns current value of the counter.
    await counters.add("counters.one", +8)
    await counters.add("counters.one", -2)
    # Increase by 1
    await counters.incr("counters.one")
    # Decrease by 1
    await counters.decr("counters.one")

    print(await counters.get("counters.one"))  # noqa: T201

    # Don't forget to call shutdown.
    await nats.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
