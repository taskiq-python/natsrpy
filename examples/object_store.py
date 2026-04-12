import asyncio
import io
from datetime import timedelta
from pathlib import Path

from natsrpy import Nats
from natsrpy.js import ObjectStoreConfig


async def main() -> None:
    """Main function to run the example."""
    nats = Nats(["nats://localhost:4222"])
    await nats.startup()

    js = await nats.jetstream()

    store = await js.object_store.create(
        ObjectStoreConfig(
            bucket="example-bucket",
            max_age=timedelta(minutes=1),
        ),
    )
    await store.put("test2.py", Path(__file__).read_bytes())
    await store.put_file("test.py", Path(__file__))

    async for obj in await store.list():
        print(obj)  # noqa: T201
        # We use BytesIO, since
        # get takes writer as it's argument.
        #
        # That happens because files can be very large,
        # and this approach allows us to stream directly
        # to files. using `open('file', 'wb') as output:`
        with io.BytesIO() as output:
            await store.get(obj.name, output)
            assert obj.size == len(output.getvalue())  # noqa: S101

        await store.delete(obj.name)

    # Don't forget to call shutdown.
    await nats.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
