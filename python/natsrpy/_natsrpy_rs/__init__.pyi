from asyncio import Future
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any, final, overload

from typing_extensions import Self

from . import exceptions, js

@final
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

@final
class IteratorSubscription:
    """Async iterator subscription for receiving NATS messages.

    Returned by :meth:`Nats.subscribe` when no callback is provided.
    Messages can be received using ``async for`` or by calling :meth:`next`
    directly.
    """

    def __aiter__(self) -> IteratorSubscription: ...
    def __anext__(self) -> Future[Message]: ...
    def next(self, timeout: float | timedelta | None = None) -> Future[Message]:
        """Receive the next message from the subscription.

        :param timeout: maximum time to wait for a message in seconds
            or as a timedelta, defaults to None (wait indefinitely).
        :return: the next message.
        :raises StopAsyncIteration: when the subscription is drained or
            unsubscribed.
        """

    def unsubscribe(self, limit: int | None = None) -> Future[None]:
        """Unsubscribe from the subject.

        :param limit: if set, automatically unsubscribe after receiving
            this many additional messages, defaults to None.
        """

    def drain(self) -> Future[None]:
        """Drain the subscription.

        Unsubscribes and flushes any remaining messages before closing.
        """

@final
class CallbackSubscription:
    """Callback-based subscription for receiving NATS messages.

    Returned by :meth:`Nats.subscribe` when a callback is provided.
    Messages are automatically delivered to the callback in a background task.
    """

    def unsubscribe(self, limit: int | None = None) -> Future[None]:
        """Unsubscribe from the subject.

        :param limit: if set, automatically unsubscribe after receiving
            this many additional messages, defaults to None.
        """

    def drain(self) -> Future[None]:
        """Drain the subscription.

        Unsubscribes and flushes any remaining messages before closing.
        """

@final
class Nats:
    """NATS client.

    Provides publish/subscribe messaging, request-reply, and JetStream
    access over a connection to one or more NATS servers.
    """

    def __new__(
        cls,
        /,
        addrs: list[str] | None = None,
        user_and_pass: tuple[str, str] | None = None,
        nkey: str | None = None,
        token: str | None = None,
        custom_inbox_prefix: str | None = None,
        read_buffer_capacity: int = ...,  # 65535 bytes
        sender_capacity: int = ...,  # 128 bytes
        max_reconnects: int | None = None,
        connection_timeout: float | timedelta = ...,  # 5 sec
        request_timeout: float | timedelta = ...,  # 10 sec
    ) -> Self:
        """Create a new NATS client instance.

        The client is not connected until :meth:`startup` is called.

        :param addrs: list of NATS server URLs, defaults to
            ``["nats://localhost:4222"]``.
        :param user_and_pass: username and password tuple for authentication.
        :param nkey: NKey seed for authentication.
        :param token: token string for authentication.
        :param custom_inbox_prefix: custom prefix for auto-generated inbox
            subjects.
        :param read_buffer_capacity: size of the read buffer in bytes,
            defaults to 65535.
        :param sender_capacity: capacity of the internal send channel,
            defaults to 128.
        :param max_reconnects: maximum number of reconnection attempts,
            None means unlimited.
        :param connection_timeout: timeout for establishing a connection
            in seconds or as a timedelta, defaults to 5 seconds.
        :param request_timeout: default timeout for request-reply operations
            in seconds or as a timedelta, defaults to 10 seconds.
        """

    def startup(self) -> Future[None]:
        """Connect to the NATS server.

        Establishes the connection using the parameters provided at
        construction time. Must be called before any publish, subscribe,
        or JetStream operations.
        """

    def shutdown(self) -> Future[None]:
        """Close the NATS connection.

        Drains all subscriptions and flushes pending data before
        disconnecting.
        """

    def publish(
        self,
        subject: str,
        payload: bytes | str | bytearray | memoryview,
        *,
        headers: dict[str, Any] | None = None,
        reply: str | None = None,
        err_on_disconnect: bool = False,
    ) -> Future[None]:
        """Publish a message to a subject.

        :param subject: subject to publish the message to.
        :param payload: message payload.
        :param headers: optional NATS headers dictionary.
        :param reply: optional reply-to subject for the request-reply
            pattern.
        :param err_on_disconnect: when True, raise an error if the client
            is disconnected, defaults to False.
        """

    def request(
        self,
        subject: str,
        payload: bytes | str | bytearray | memoryview,
        *,
        headers: dict[str, Any] | None = None,
        inbox: str | None = None,
        timeout: float | timedelta | None = None,
    ) -> Future[Message]:
        """Send a request and discard the response.

        :param subject: subject to send the request to.
        :param payload: request payload.
        :param headers: optional NATS headers dictionary.
        :param inbox: custom inbox subject for the reply, auto-generated
            if None.
        :param timeout: maximum time to wait for a response in seconds
            or as a timedelta, defaults to the client request_timeout.
        :return: response message.
        """

    def drain(self) -> Future[None]:
        """Drain the connection.

        Gracefully closes all subscriptions and flushes pending messages.
        """

    def flush(self) -> Future[None]:
        """Flush the connection.

        Waits until all pending messages have been sent to the server.
        """

    @overload
    def subscribe(
        self,
        subject: str,
        callback: Callable[[Message], Awaitable[None]],
        queue: str | None = None,
    ) -> Future[CallbackSubscription]: ...
    @overload
    def subscribe(
        self,
        subject: str,
        callback: None = None,
        queue: str | None = None,
    ) -> Future[IteratorSubscription]: ...
    def jetstream(
        self,
        *,
        domain: str | None = None,
        api_prefix: str | None = None,
        timeout: float | timedelta | None = None,
        ack_timeout: float | timedelta | None = None,
        concurrency_limit: int | None = None,
        max_ack_inflight: int | None = None,
        backpressure_on_inflight: bool | None = None,
    ) -> Future[js.JetStream]:
        """Create a JetStream context.

        :param domain: JetStream domain to use.
        :param api_prefix: custom JetStream API prefix, cannot be used
            together with *domain*.
        :param timeout: default request timeout for JetStream operations
            in seconds or as a timedelta.
        :param ack_timeout: acknowledgement timeout for consumers in seconds
            or as a timedelta.
        :param concurrency_limit: maximum number of concurrent JetStream
            operations.
        :param max_ack_inflight: maximum number of unacknowledged messages
            in flight.
        :param backpressure_on_inflight: when True, apply backpressure when
            the in-flight limit is reached.
        :return: a JetStream context.
        """

__all__ = [
    "CallbackSubscription",
    "IteratorSubscription",
    "Message",
    "Nats",
    "exceptions",
    "js",
]
