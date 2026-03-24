from datetime import datetime, timedelta
from typing import Any, Literal, overload

from .managers import KVManager, ObjectStoreManager, StreamsManager

class Publication:
    stream: str
    sequence: int
    domain: str
    duplicate: bool
    value: str | None

class JetStream:
    @overload
    async def publish(
        self,
        subject: str,
        payload: str | bytes | bytearray | memoryview,
        *,
        headers: dict[str, str] | None = None,
        err_on_disconnect: bool = False,
        wait: Literal[True],
    ) -> Publication: ...
    @overload
    async def publish(
        self,
        subject: str,
        payload: str | bytes | bytearray | memoryview,
        *,
        headers: dict[str, str] | None = None,
        err_on_disconnect: bool = False,
        wait: Literal[False] = False,
    ) -> None: ...
    @overload
    async def publish(
        self,
        subject: str,
        payload: str | bytes | bytearray | memoryview,
        *,
        headers: dict[str, str] | None = None,
        err_on_disconnect: bool = False,
        wait: bool = False,
    ) -> Publication | None: ...
    @property
    def kv(self) -> KVManager: ...
    @property
    def streams(self) -> StreamsManager: ...
    @property
    def object_store(self) -> ObjectStoreManager: ...

class JetStreamMessage:
    @property
    def subject(self) -> str: ...
    @property
    def reply(self) -> str | None: ...
    @property
    def payload(self) -> bytes: ...
    @property
    def headers(self) -> dict[str, Any]: ...
    @property
    def domain(self) -> str | None: ...
    @property
    def acc_hash(self) -> str | None: ...
    @property
    def stream(self) -> str: ...
    @property
    def consumer(self) -> str: ...
    @property
    def stream_sequence(self) -> int: ...
    @property
    def consumer_sequence(self) -> int: ...
    @property
    def delivered(self) -> int: ...
    @property
    def pending(self) -> int: ...
    @property
    def published(self) -> datetime: ...
    @property
    def token(self) -> str | None: ...
    async def ack(self, double: bool = False) -> None:
        """
        Acknowledge that a message was handled.

        :param double: whether to wait for server response, defaults to False
        """

    async def nack(
        self,
        delay: float | timedelta | None = None,
        double: bool = False,
    ) -> None:
        """
        Negative acknowledgement.

        Signals that the message will not be processed now
        and processing can move onto the next message, NAK'd
        message will be retried.

        :param duration: time, defaults to None
        :param double: whether to wait for server response, defaults to False
        """

    async def progress(self, double: bool = False) -> None:
        """
        Progress acknowledgement.

        Singnals that the mesasge is being handled right now.
        Sending this request before the AckWait will extend wait period
        before redelivering a message.

        :param double: whether to wait for server response, defaults to False
        """

    async def next(self, double: bool = False) -> None:
        """
        Next acknowledgement.

        Only applies to pull consumers!
        Acknowledges message processing and instructs server to send
        delivery of the next message to the reply subject.

        :param double: whether to wait for server response, defaults to False
        """

    async def term(self, double: bool = False) -> None:
        """
        Term acknowledgement.

        Instructs server to stop redelivering message.
        Useful to stop redelivering a message after multiple NACKs.

        :param double: whether to wait for server response, defaults to False
        """
