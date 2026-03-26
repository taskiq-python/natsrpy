import asyncio

from natsrpy import Nats
from natsrpy.js import KVConfig


async def main() -> None:
    """Main function to run the example."""
    nats = Nats(["nats://localhost:4222"])
    await nats.startup()

    js = await nats.jetstream()

    kv = await js.kv.create_or_update(KVConfig(bucket="kv-example"))

    watcher = await kv.watch("test-key")

    await kv.put("test-key", "one")
    await kv.put("test-key", b"two")

    # To obtain bytes value.
    value = await kv.get("test-key")
    if value:
        print("[VALUE]", value.decode())  # noqa: T201
    # To get kv-entry with all
    # the metadata.
    entry = await kv.entry("test-key")
    if entry:
        print("[ENTRY]", entry)  # noqa: T201

    await kv.delete("test-key")

    # Alternatively you can
    # use await watcher.next()
    async for event in watcher:
        print("[EVENT]", event)  # noqa: T201
        break

    await js.kv.delete(kv.name)

    # Don't forget to call shutdown.
    await nats.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
