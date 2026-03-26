import uuid

import pytest
from natsrpy.js import CounterEntry, Counters, CountersConfig, JetStream


async def test_counters_create(js: JetStream) -> None:
    name = f"test-cnt-create-{uuid.uuid4().hex[:8]}"
    config = CountersConfig(name=name, subjects=[f"{name}.>"])
    counters = await js.counters.create(config)
    try:
        assert isinstance(counters, Counters)
    finally:
        await js.counters.delete(name)


async def test_counters_create_or_update(js: JetStream) -> None:
    name = f"test-cnt-cou-{uuid.uuid4().hex[:8]}"
    config = CountersConfig(name=name, subjects=[f"{name}.>"])
    counters = await js.counters.create_or_update(config)
    try:
        assert isinstance(counters, Counters)
        config.description = "updated"
        counters2 = await js.counters.create_or_update(config)
        assert isinstance(counters2, Counters)
    finally:
        await js.counters.delete(name)


async def test_counters_get(js: JetStream) -> None:
    name = f"test-cnt-get-{uuid.uuid4().hex[:8]}"
    config = CountersConfig(name=name, subjects=[f"{name}.>"])
    await js.counters.create(config)
    try:
        counters = await js.counters.get(name)
        assert isinstance(counters, Counters)
    finally:
        await js.counters.delete(name)


async def test_counters_delete(js: JetStream) -> None:
    name = f"test-cnt-del-{uuid.uuid4().hex[:8]}"
    config = CountersConfig(name=name, subjects=[f"{name}.>"])
    await js.counters.create(config)
    result = await js.counters.delete(name)
    assert result is True


async def test_counters_update(js: JetStream) -> None:
    name = f"test-cnt-upd-{uuid.uuid4().hex[:8]}"
    config = CountersConfig(name=name, subjects=[f"{name}.>"])
    await js.counters.create(config)
    try:
        update_cfg = CountersConfig(
            name=name,
            subjects=[f"{name}.>"],
            description="updated description",
        )
        counters = await js.counters.update(update_cfg)
        assert isinstance(counters, Counters)
    finally:
        await js.counters.delete(name)


async def test_counters_incr(js: JetStream) -> None:
    name = f"test-cnt-incr-{uuid.uuid4().hex[:8]}"
    subj = f"{name}.hits"
    config = CountersConfig(name=name, subjects=[f"{name}.>"])
    counters = await js.counters.create(config)
    try:
        value = await counters.incr(subj)
        assert value == 1
    finally:
        await js.counters.delete(name)


async def test_counters_decr(js: JetStream) -> None:
    name = f"test-cnt-decr-{uuid.uuid4().hex[:8]}"
    subj = f"{name}.hits"
    config = CountersConfig(name=name, subjects=[f"{name}.>"])
    counters = await js.counters.create(config)
    try:
        value = await counters.decr(subj)
        assert value == -1
    finally:
        await js.counters.delete(name)


async def test_counters_add(js: JetStream) -> None:
    name = f"test-cnt-add-{uuid.uuid4().hex[:8]}"
    subj = f"{name}.hits"
    config = CountersConfig(name=name, subjects=[f"{name}.>"])
    counters = await js.counters.create(config)
    try:
        value = await counters.add(subj, 10)
        assert value == 10
    finally:
        await js.counters.delete(name)


async def test_counters_add_negative(js: JetStream) -> None:
    name = f"test-cnt-addneg-{uuid.uuid4().hex[:8]}"
    subj = f"{name}.hits"
    config = CountersConfig(name=name, subjects=[f"{name}.>"])
    counters = await js.counters.create(config)
    try:
        value = await counters.add(subj, -5)
        assert value == -5
    finally:
        await js.counters.delete(name)


async def test_counters_get_entry(js: JetStream) -> None:
    name = f"test-cnt-gete-{uuid.uuid4().hex[:8]}"
    subj = f"{name}.hits"
    config = CountersConfig(name=name, subjects=[f"{name}.>"])
    counters = await js.counters.create(config)
    try:
        await counters.incr(subj)
        entry = await counters.get(subj)
        assert isinstance(entry, CounterEntry)
        assert entry.subject == subj
        assert entry.value == 1
    finally:
        await js.counters.delete(name)


async def test_counter_entry_attributes(js: JetStream) -> None:
    name = f"test-cnt-attr-{uuid.uuid4().hex[:8]}"
    subj = f"{name}.hits"
    config = CountersConfig(name=name, subjects=[f"{name}.>"])
    counters = await js.counters.create(config)
    try:
        await counters.add(subj, 5)
        entry = await counters.get(subj)
        assert isinstance(entry.subject, str)
        assert isinstance(entry.value, int)
        assert isinstance(entry.sources, dict)
        assert entry.increment is None or isinstance(entry.increment, int)
    finally:
        await js.counters.delete(name)


async def test_counters_multiple_increments(js: JetStream) -> None:
    name = f"test-cnt-multi-{uuid.uuid4().hex[:8]}"
    subj = f"{name}.hits"
    config = CountersConfig(name=name, subjects=[f"{name}.>"])
    counters = await js.counters.create(config)
    try:
        val1 = await counters.incr(subj)
        val2 = await counters.incr(subj)
        val3 = await counters.incr(subj)
        assert val1 == 1
        assert val2 == 2
        assert val3 == 3
        entry = await counters.get(subj)
        assert entry.value == 3
    finally:
        await js.counters.delete(name)


async def test_counters_incr_then_decr(js: JetStream) -> None:
    name = f"test-cnt-incdec-{uuid.uuid4().hex[:8]}"
    subj = f"{name}.hits"
    config = CountersConfig(name=name, subjects=[f"{name}.>"])
    counters = await js.counters.create(config)
    try:
        await counters.incr(subj)
        await counters.incr(subj)
        await counters.decr(subj)
        entry = await counters.get(subj)
        assert entry.value == 1
    finally:
        await js.counters.delete(name)


async def test_counters_separate_subjects(js: JetStream) -> None:
    name = f"test-cnt-sep-{uuid.uuid4().hex[:8]}"
    subj_a = f"{name}.a"
    subj_b = f"{name}.b"
    config = CountersConfig(name=name, subjects=[f"{name}.>"])
    counters = await js.counters.create(config)
    try:
        await counters.add(subj_a, 10)
        await counters.add(subj_b, 20)
        entry_a = await counters.get(subj_a)
        entry_b = await counters.get(subj_b)
        assert entry_a.value == 10
        assert entry_b.value == 20
    finally:
        await js.counters.delete(name)


async def test_counters_get_nonexistent_key(js: JetStream) -> None:
    name = f"test-cnt-nokey-{uuid.uuid4().hex[:8]}"
    config = CountersConfig(name=name, subjects=[f"{name}.>"])
    counters = await js.counters.create(config)
    try:
        with pytest.raises(Exception):
            await counters.get(f"{name}.nonexistent")
    finally:
        await js.counters.delete(name)


async def test_counters_config_description(js: JetStream) -> None:
    name = f"test-cnt-desc-{uuid.uuid4().hex[:8]}"
    config = CountersConfig(
        name=name,
        subjects=[f"{name}.>"],
        description="A test counters stream",
    )
    counters = await js.counters.create(config)
    try:
        assert isinstance(counters, Counters)
    finally:
        await js.counters.delete(name)


async def test_counters_config_defaults() -> None:
    config = CountersConfig(name="test", subjects=["test.>"])
    assert config.name == "test"
    assert config.subjects == ["test.>"]
    assert config.description is None
    assert config.max_bytes is not None
    assert config.max_messages is not None
