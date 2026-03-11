from typing import Any

class Message:
    subject: str
    reply: str | None
    payload: bytes
    headers: dict[str, Any]
    status: int | None
    description: str | None
    length: int

    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
