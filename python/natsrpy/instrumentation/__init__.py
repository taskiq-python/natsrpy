"""
Instrument `natsrpy`_ to trace messages.

.. natsrpy: https://pypi.org/project/natsrpy/

Usage
-----

* Run instrumented task

.. code:: python

    import asyncio

    from natsrpy import Nats
    from natsrpy.instrumentation import NatsrpyInstrumentor

    NatsrpyInstrumentor().instrument()


    async def main() -> None:
        nats = Nats()
        await nats.startup()
        await nats.publish("test", b"test")
        await nats.shutdown()


    if __name__ == "__main__":
        asyncio.run(main())

API
---
"""

import logging
from collections.abc import Collection
from importlib import metadata
from typing import Any

from .nats_core import NatsCoreInstrumentator

try:
    import opentelemetry  # noqa: F401
except ImportError as exc:
    raise ImportError(
        "Cannot instrument. Please install 'natsrpy[opentelemetry]'.",
    ) from exc

from opentelemetry import trace
from opentelemetry.instrumentation.instrumentor import (
    BaseInstrumentor,
)

_INSTRUMENTATION_MODULE_NAME = "opentelemetry.instrumentation.natsrpy"

logger = logging.getLogger("natsrpy.opentelemetry")


class NatsrpyInstrumentor(BaseInstrumentor):  # type: ignore
    """OpenTelemetry instrumentor for Natsrpy."""

    def __init__(self) -> None:
        super().__init__()

    def instrumentation_dependencies(self) -> Collection[str]:
        """This function tells which library this instrumentor instruments."""
        return ("natsrpy >= 0.0.0",)

    def _instrument(self, **kwargs: Any) -> None:
        tracer_provider = kwargs.get("tracer_provider")
        tracer = trace.get_tracer(
            _INSTRUMENTATION_MODULE_NAME,
            metadata.version("natsrpy"),
            tracer_provider,
        )
        NatsCoreInstrumentator(tracer).instrument()

    def _uninstrument(self, **kwargs: Any) -> None:
        NatsCoreInstrumentator.uninstrument()
