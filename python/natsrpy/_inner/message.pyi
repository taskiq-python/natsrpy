from typing import Any

class Message:
    subject: str
    reply: str | None
    payload: bytes
    headers: dict[str, Any]
    status: int | None
    description: str | None
    length: int
