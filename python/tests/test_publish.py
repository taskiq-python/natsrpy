import uuid
from typing import Any

import pytest
from natsrpy import Nats


async def test_publish_simple(nats: Nats) -> None:
    subj = uuid.uuid4().hex
    payload = uuid.uuid4().hex.encode()
    sub = await nats.subscribe(subject=subj)
    await nats.publish(subj, payload)
    message = await anext(sub)
    assert message.payload == payload


@pytest.mark.parametrize(
    "headers",
    [
        {"test": "string-headers"},
        {"test": ["multi", "value"]},
    ],
)
async def test_publis_headers(nats: Nats, headers: dict[str, Any]) -> None:
    subj = uuid.uuid4().hex
    payload = uuid.uuid4().hex.encode()
    sub = await nats.subscribe(subject=subj)
    await nats.publish(subj, payload, headers=headers)
    message = await anext(sub)
    assert message.payload == payload
    assert message.headers == headers
