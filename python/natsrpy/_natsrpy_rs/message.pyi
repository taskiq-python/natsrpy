from typing import Any

class Message:
    """
    Simple NATS message.

    Attributes:
        subject: subject where message was published
        reply: subject where reply should be sent, if any
        payload: message payload
        headers: dictionary of message headers,
            every value can be a simple value or a list.
        status: status is used for reply messages to indicate the status of the reply.
            It is None for regular messages.
        description: message description is used for reply messages to
            provide additional information about the status.
        length: a length of the message payload in bytes.
    """

    subject: str
    reply: str | None
    payload: bytes
    headers: dict[str, Any]
    status: int | None
    description: str | None
    length: int
