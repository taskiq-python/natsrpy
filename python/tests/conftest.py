import os
from collections.abc import AsyncGenerator

import pytest
from natsrpy import Nats


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """
    Anyio backend.

    Backend for anyio pytest plugin.
    :return: backend name.
    """
    return "asyncio"


@pytest.fixture(scope="session")
def nats_url() -> str:
    return os.environ.get("NATS_URL", "localhost:4222")


@pytest.fixture(scope="session")
async def nats(nats_url: str) -> AsyncGenerator[Nats, None]:
    nats = Nats(addrs=[nats_url])
    await nats.startup()

    yield nats

    await nats.shutdown()
