
class StorageType:
    FILE: "StorageType"
    MEMORY: "StorageType"

class KVConfig:
    def __init__(
        self,
        bucket: str,
        description: str | None = None,
        max_value_size: int | None = None,
        history:int|None=None,
        max_age:float |None=None,
        max_bytes:int |None=None,
        storage:StorageType|None=None,
        num_replicas: int |None=None,
        republish:bool |None=None,
        mirror:|None=None,
        sources:|None=None,
        mirror_direct:|None=None,
        compression:|None=None,
        placement:|None=None,
        limit_markers:|None=None,
    ) -> None: ...

class KeyValue:
    async def get(self, key: str) -> bytes | None: ...
    async def put(self, key: str, value: bytes) -> int: ...
