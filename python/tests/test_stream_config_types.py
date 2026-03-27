from datetime import timedelta

from natsrpy.js import (
    ConsumerLimits,
    External,
    Placement,
    Source,
)


async def test_external_construct() -> None:
    ext = External(api_prefix="$JS.API")
    assert ext.api_prefix == "$JS.API"
    assert ext.delivery_prefix is None


async def test_external_with_delivery_prefix() -> None:
    ext = External(api_prefix="$JS.API", delivery_prefix="$JS.DELIVER")
    assert ext.api_prefix == "$JS.API"
    assert ext.delivery_prefix == "$JS.DELIVER"


async def test_external_setters() -> None:
    ext = External(api_prefix="$JS.API")
    ext.api_prefix = "$JS.NEW"
    assert ext.api_prefix == "$JS.NEW"
    ext.delivery_prefix = "$JS.DEL"
    assert ext.delivery_prefix == "$JS.DEL"


async def test_source_construct_minimal() -> None:
    src = Source(name="src-stream")
    assert src.name == "src-stream"
    assert src.filter_subject is None
    assert src.external is None
    assert src.start_sequence is None
    assert src.domain is None


async def test_source_with_filter() -> None:
    src = Source(name="src-stream", filter_subject="test.>")
    assert src.name == "src-stream"
    assert src.filter_subject == "test.>"


async def test_source_with_external() -> None:
    ext = External(api_prefix="$JS.API")
    src = Source(name="src-stream", external=ext)
    assert src.name == "src-stream"
    assert src.external is not None


async def test_source_setters() -> None:
    src = Source(name="src-stream")
    src.name = "new-stream"
    assert src.name == "new-stream"
    src.filter_subject = "filter.>"
    assert src.filter_subject == "filter.>"


async def test_placement_construct() -> None:
    p = Placement(cluster="us-east", tags=["fast", "ssd"])
    assert p.cluster == "us-east"
    assert p.tags == ["fast", "ssd"]


async def test_placement_defaults() -> None:
    p = Placement()
    assert p.cluster is None
    # default is empty list
    assert p.tags == []


async def test_placement_setters() -> None:
    p = Placement()
    p.cluster = "eu-west"
    assert p.cluster == "eu-west"
    p.tags = ["backup"]
    assert p.tags == ["backup"]


async def test_consumer_limits_construct() -> None:
    cl = ConsumerLimits(
        inactive_threshold=timedelta(seconds=30),
        max_ack_pending=100,
    )
    # ConsumerLimits doesn't expose its fields as Python getters,
    # but the constructor should succeed without errors.
    assert cl is not None


async def test_consumer_limits_construct_with_float() -> None:
    cl = ConsumerLimits(
        inactive_threshold=timedelta(seconds=30),
        max_ack_pending=50,
    )
    assert cl is not None
