import uuid

from natsrpy.js import (
    JetStream,
    KeyValue,
    KVConfig,
)


async def test_kv_manager_update(js: JetStream) -> None:
    bucket = f"test-kv-mgrupd-{uuid.uuid4().hex[:8]}"
    config = KVConfig(bucket=bucket, description="original")
    await js.kv.create(config)
    try:
        config.description = "updated description"
        updated_kv = await js.kv.update(config)
        assert isinstance(updated_kv, KeyValue)
        assert updated_kv.name == bucket
    finally:
        await js.kv.delete(bucket)
