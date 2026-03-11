class StorageType:
    FILE: "StorageType"
    MEMORY: "StorageType"

class External:
    def __init__(
        self,
        api_prefix: str,
        delivery_prefix: str | None = None,
    ) -> None: ...

class SubjectTransform:
    def __init__(
        self,
        source: str,
        destination: str,
    ) -> None: ...

class Source:
    def __init__(
        self,
        name: str,
        filter_subject: str | None = None,
        external: External | None = None,
        start_sequence: int | None = None,
        start_time: int | None = None,
        domain: str | None = None,
        subject_transforms: SubjectTransform | None = None,
    ) -> None: ...

class Placement:
    def __init__(
        self,
        cluster: str | None = None,
        tags: list[str] | None = None,
    ) -> None: ...

class Republish:
    pass
    def __init__(
        self,
        source: str | None = None,
        destination: str | None = None,
        headers_only: str | None = None,
    ) -> None: ...
