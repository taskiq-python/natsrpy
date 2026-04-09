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
import os
from collections.abc import Collection
from importlib import metadata
from typing import Any

from .js_consumer import JSConsumerInstrumentation
from .js_publish import JSPublishInstrumentation
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
        capture_body = (
            os.environ.get(
                "OTEL_PYTHON_NATSRPY_CAPTURE_BODY",
                str(kwargs.get("capture_body", False)),
            ).lower()
            == "true"
        )
        capture_headers = (
            os.environ.get(
                "OTEL_PYTHON_NATSRPY_CAPTURE_HEADERS",
                str(kwargs.get("capture_headers", False)),
            ).lower()
            == "true"
        )
        tracer = trace.get_tracer(
            _INSTRUMENTATION_MODULE_NAME,
            metadata.version("natsrpy"),
            tracer_provider,
        )
        NatsCoreInstrumentator(
            tracer,
            capture_body=capture_body,
            capture_headers=capture_headers,
        ).instrument()
        JSConsumerInstrumentation(
            tracer,
            capture_body=capture_body,
            capture_headers=capture_headers,
        ).instrument()
        JSPublishInstrumentation(
            tracer,
            capture_body=capture_body,
            capture_headers=capture_headers,
        ).instrument()

    def _uninstrument(self, **kwargs: Any) -> None:
        NatsCoreInstrumentator.uninstrument()
        JSConsumerInstrumentation.uninstrument()
        JSPublishInstrumentation.uninstrument()
