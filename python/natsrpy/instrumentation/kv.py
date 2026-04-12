from typing import Any

from opentelemetry import trace
from opentelemetry.instrumentation.utils import is_instrumentation_enabled, unwrap
from opentelemetry.trace import SpanKind, Tracer
from typing_extensions import Self
from wrapt import ObjectProxy, wrap_function_wrapper

from natsrpy.js import KeyValue, KVEntry, KVEntryIterator

from .span_builder import SpanAction, SpanBuilder

_KV_MODULE = "natsrpy._natsrpy_rs.js.kv"


class KVEntryIteratorProxy(ObjectProxy):  # type: ignore
    """Proxy for KVEntryIterator returned by watch and history methods."""

    def __init__(
        self,
        wrapped: KVEntryIterator,
        tracer: Tracer,
        bucket: str,
        capture_body: bool,
    ) -> None:
        super().__init__(wrapped)
        self._self_tracer = tracer
        self._self_bucket = bucket
        self._self_capture_body = capture_body

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> KVEntry:
        entry: KVEntry = await anext(self.__wrapped__)
        if not is_instrumentation_enabled():
            return entry
        span = (
            SpanBuilder(self._self_tracer, SpanKind.CONSUMER, SpanAction.RECEIVE)
            .with_kv_bucket(self._self_bucket)
            .with_kv_key(entry.key)
            .with_kv_value(entry.value, capture_body=self._self_capture_body)
            .build()
        )
        with trace.use_span(span, end_on_exit=True):
            pass
        return entry


class KVInstrumentation:
    """Instrument KeyValue store operations."""

    def __init__(
        self,
        tracer: Tracer,
        capture_body: bool = False,
    ) -> None:
        self.tracer = tracer
        self.capture_body = capture_body

    def instrument(self) -> None:
        """Setup instrumentation for all KeyValue methods."""
        self._instrument_put()
        self._instrument_create()
        self._instrument_update()
        self._instrument_delete()
        self._instrument_purge()
        self._instrument_get()
        self._instrument_entry()
        self._instrument_history()
        self._instrument_watch_methods()
        self._instrument_keys()

    @staticmethod
    def uninstrument() -> None:
        """Remove instrumentation from all KeyValue methods."""
        for method in (
            "put",
            "create",
            "update",
            "delete",
            "purge",
            "get",
            "entry",
            "history",
            "watch",
            "watch_with_history",
            "watch_all",
            "watch_many",
            "watch_many_with_history",
            "keys",
        ):
            unwrap(KeyValue, method)

    def _instrument_put(self) -> None:
        tracer = self.tracer
        capture_body = self.capture_body

        async def _wrapped(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            key: str = args[0]
            value: bytes | str = args[1]
            span = (
                SpanBuilder(tracer, SpanKind.PRODUCER, SpanAction.KV_PUT)
                .with_kv_bucket(instance.name)
                .with_kv_key(key)
                .with_kv_value(value, capture_body=capture_body)
                .build()
            )
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, instance, args, kwargs)

        wrap_function_wrapper(_KV_MODULE, "KeyValue.put", decorator)

    def _instrument_create(self) -> None:
        tracer = self.tracer
        capture_body = self.capture_body

        async def _wrapped(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            key: str = args[0]
            value: bytes | str = args[1]
            span = (
                SpanBuilder(tracer, SpanKind.PRODUCER, SpanAction.KV_CREATE)
                .with_kv_bucket(instance.name)
                .with_kv_key(key)
                .with_kv_value(value, capture_body=capture_body)
                .build()
            )
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, instance, args, kwargs)

        wrap_function_wrapper(_KV_MODULE, "KeyValue.create", decorator)

    def _instrument_update(self) -> None:
        tracer = self.tracer
        capture_body = self.capture_body

        async def _wrapped(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            key: str = args[0]
            value: bytes | str = args[1]
            span = (
                SpanBuilder(tracer, SpanKind.PRODUCER, SpanAction.KV_UPDATE)
                .with_kv_bucket(instance.name)
                .with_kv_key(key)
                .with_kv_value(value, capture_body=capture_body)
                .build()
            )
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, instance, args, kwargs)

        wrap_function_wrapper(_KV_MODULE, "KeyValue.update", decorator)

    def _instrument_delete(self) -> None:
        tracer = self.tracer

        async def _wrapped(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            key: str = args[0]
            span = (
                SpanBuilder(tracer, SpanKind.PRODUCER, SpanAction.KV_DELETE)
                .with_kv_bucket(instance.name)
                .with_kv_key(key)
                .build()
            )
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, instance, args, kwargs)

        wrap_function_wrapper(_KV_MODULE, "KeyValue.delete", decorator)

    def _instrument_purge(self) -> None:
        tracer = self.tracer

        async def _wrapped(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            key: str = args[0]
            span = (
                SpanBuilder(tracer, SpanKind.PRODUCER, SpanAction.KV_PURGE)
                .with_kv_bucket(instance.name)
                .with_kv_key(key)
                .build()
            )
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, instance, args, kwargs)

        wrap_function_wrapper(_KV_MODULE, "KeyValue.purge", decorator)

    def _instrument_get(self) -> None:
        tracer = self.tracer

        async def _wrapped(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            key: str = args[0]
            span = (
                SpanBuilder(tracer, SpanKind.CLIENT, SpanAction.KV_GET)
                .with_kv_bucket(instance.name)
                .with_kv_key(key)
                .build()
            )
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, instance, args, kwargs)

        wrap_function_wrapper(_KV_MODULE, "KeyValue.get", decorator)

    def _instrument_entry(self) -> None:
        tracer = self.tracer

        async def _wrapped(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            key: str = args[0]
            span = (
                SpanBuilder(tracer, SpanKind.CLIENT, SpanAction.KV_ENTRY)
                .with_kv_bucket(instance.name)
                .with_kv_key(key)
                .build()
            )
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, instance, args, kwargs)

        wrap_function_wrapper(_KV_MODULE, "KeyValue.entry", decorator)

    def _instrument_history(self) -> None:
        tracer = self.tracer
        capture_body = self.capture_body

        async def _wrapped(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            iterator: KVEntryIterator = await wrapper(*args, **kwargs)
            return KVEntryIteratorProxy(iterator, tracer, instance.name, capture_body)

        def decorator(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, instance, args, kwargs)

        wrap_function_wrapper(_KV_MODULE, "KeyValue.history", decorator)

    def _instrument_watch_methods(self) -> None:
        tracer = self.tracer
        capture_body = self.capture_body

        def make_decorator() -> Any:
            async def _wrapped(
                wrapper: Any,
                instance: KeyValue,
                args: tuple[Any, ...],
                kwargs: dict[str, Any],
            ) -> Any:
                if not is_instrumentation_enabled():
                    return await wrapper(*args, **kwargs)
                iterator: KVEntryIterator = await wrapper(*args, **kwargs)
                return KVEntryIteratorProxy(
                    iterator,
                    tracer,
                    instance.name,
                    capture_body,
                )

            def decorator(
                wrapper: Any,
                instance: KeyValue,
                args: tuple[Any, ...],
                kwargs: dict[str, Any],
            ) -> Any:
                return _wrapped(wrapper, instance, args, kwargs)

            return decorator

        for method in (
            "watch",
            "watch_with_history",
            "watch_all",
            "watch_many",
            "watch_many_with_history",
        ):
            wrap_function_wrapper(_KV_MODULE, f"KeyValue.{method}", make_decorator())

    def _instrument_keys(self) -> None:
        tracer = self.tracer

        async def _wrapped(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            span = (
                SpanBuilder(tracer, SpanKind.CLIENT, SpanAction.KV_KEYS)
                .with_kv_bucket(instance.name)
                .build()
            )
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            instance: KeyValue,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, instance, args, kwargs)

        wrap_function_wrapper(_KV_MODULE, "KeyValue.keys", decorator)
