from typing import Any

from opentelemetry import trace
from opentelemetry.instrumentation.utils import is_instrumentation_enabled, unwrap
from opentelemetry.trace import SpanKind, Tracer
from typing_extensions import Self
from wrapt import ObjectProxy, wrap_function_wrapper

from natsrpy.js import ObjectInfo, ObjectInfoIterator, ObjectStore

from .span_builder import SpanAction, SpanBuilder

_OS_MODULE = "natsrpy._natsrpy_rs.js.object_store"


class ObjectInfoIteratorProxy(ObjectProxy):  # type: ignore
    """Proxy for ObjectInfoIterator returned by watch and list methods."""

    def __init__(
        self,
        wrapped: ObjectInfoIterator,
        tracer: Tracer,
    ) -> None:
        super().__init__(wrapped)
        self._self_tracer = tracer

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> ObjectInfo:
        info: ObjectInfo = await anext(self.__wrapped__)
        if not is_instrumentation_enabled():
            return info
        span = (
            SpanBuilder(self._self_tracer, SpanKind.CONSUMER, SpanAction.RECEIVE)
            .with_object_name(info.name)
            .with_object_size(info.size)
            .build()
        )
        with trace.use_span(span, end_on_exit=True):
            pass
        return info


class ObjectStoreInstrumentation:
    """Instrument ObjectStore operations."""

    def __init__(
        self,
        tracer: Tracer,
        capture_body: bool = False,
    ) -> None:
        self.tracer = tracer
        self.capture_body = capture_body

    def instrument(self) -> None:
        """Setup instrumentation for all ObjectStore methods."""
        self._instrument_put()
        self._instrument_put_file()
        self._instrument_get()
        self._instrument_delete()
        self._instrument_seal()
        self._instrument_get_info()
        self._instrument_watch()
        self._instrument_list()
        self._instrument_link_bucket()
        self._instrument_link_object()
        self._instrument_update_metadata()

    @staticmethod
    def uninstrument() -> None:
        """Remove instrumentation from all ObjectStore methods."""
        for method in (
            "put",
            "put_file",
            "get",
            "delete",
            "seal",
            "get_info",
            "watch",
            "list",
            "link_bucket",
            "link_object",
            "update_metadata",
        ):
            unwrap(ObjectStore, method)

    def _instrument_put(self) -> None:
        tracer = self.tracer
        capture_body = self.capture_body

        async def _wrapped(
            wrapper: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            name: str = args[0]
            value: bytes | str = args[1]
            span = (
                SpanBuilder(tracer, SpanKind.PRODUCER, SpanAction.OBJ_PUT)
                .with_object_name(name)
                .with_object_size(len(value))
                .build()
            )
            if capture_body:
                span.set_attribute("nats.object_store.value", value)
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            _: ObjectStore,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, args, kwargs)

        wrap_function_wrapper(_OS_MODULE, "ObjectStore.put", decorator)

    def _instrument_put_file(self) -> None:
        tracer = self.tracer

        async def _wrapped(
            wrapper: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            name: str = args[0]
            span = (
                SpanBuilder(tracer, SpanKind.PRODUCER, SpanAction.OBJ_PUT)
                .with_object_name(name)
                .build()
            )
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            _: ObjectStore,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, args, kwargs)

        wrap_function_wrapper(_OS_MODULE, "ObjectStore.put_file", decorator)

    def _instrument_get(self) -> None:
        tracer = self.tracer

        async def _wrapped(
            wrapper: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            name: str = args[0]
            span = (
                SpanBuilder(tracer, SpanKind.CLIENT, SpanAction.OBJ_GET)
                .with_object_name(name)
                .build()
            )
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            _: ObjectStore,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, args, kwargs)

        wrap_function_wrapper(_OS_MODULE, "ObjectStore.get", decorator)

    def _instrument_delete(self) -> None:
        tracer = self.tracer

        async def _wrapped(
            wrapper: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            name: str = args[0]
            span = (
                SpanBuilder(tracer, SpanKind.PRODUCER, SpanAction.OBJ_DELETE)
                .with_object_name(name)
                .build()
            )
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            _: ObjectStore,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, args, kwargs)

        wrap_function_wrapper(_OS_MODULE, "ObjectStore.delete", decorator)

    def _instrument_seal(self) -> None:
        tracer = self.tracer

        async def _wrapped(
            wrapper: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            span = SpanBuilder(tracer, SpanKind.PRODUCER, SpanAction.OBJ_SEAL).build()
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            _: ObjectStore,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, args, kwargs)

        wrap_function_wrapper(_OS_MODULE, "ObjectStore.seal", decorator)

    def _instrument_get_info(self) -> None:
        tracer = self.tracer

        async def _wrapped(
            wrapper: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            name: str = args[0]
            span = (
                SpanBuilder(tracer, SpanKind.CLIENT, SpanAction.OBJ_INFO)
                .with_object_name(name)
                .build()
            )
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            _: ObjectStore,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, args, kwargs)

        wrap_function_wrapper(_OS_MODULE, "ObjectStore.get_info", decorator)

    def _instrument_watch(self) -> None:
        tracer = self.tracer

        async def _wrapped(
            wrapper: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            iterator: ObjectInfoIterator = await wrapper(*args, **kwargs)
            return ObjectInfoIteratorProxy(iterator, tracer)

        def decorator(
            wrapper: Any,
            _: ObjectStore,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, args, kwargs)

        wrap_function_wrapper(_OS_MODULE, "ObjectStore.watch", decorator)

    def _instrument_list(self) -> None:
        tracer = self.tracer

        async def _wrapped(
            wrapper: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            iterator: ObjectInfoIterator = await wrapper(*args, **kwargs)
            return ObjectInfoIteratorProxy(iterator, tracer)

        def decorator(
            wrapper: Any,
            _: ObjectStore,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, args, kwargs)

        wrap_function_wrapper(_OS_MODULE, "ObjectStore.list", decorator)

    def _instrument_link_bucket(self) -> None:
        tracer = self.tracer

        async def _wrapped(
            wrapper: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            src_bucket: str = args[0]
            dest: str = args[1]
            span = (
                SpanBuilder(tracer, SpanKind.CLIENT, SpanAction.OBJ_LINK)
                .with_object_name(dest)
                .build()
            )
            span.set_attribute("nats.object_store.link_source", src_bucket)
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            _: ObjectStore,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, args, kwargs)

        wrap_function_wrapper(_OS_MODULE, "ObjectStore.link_bucket", decorator)

    def _instrument_link_object(self) -> None:
        tracer = self.tracer

        async def _wrapped(
            wrapper: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            src: str = args[0]
            dest: str = args[1]
            span = (
                SpanBuilder(tracer, SpanKind.CLIENT, SpanAction.OBJ_LINK)
                .with_object_name(dest)
                .build()
            )
            span.set_attribute("nats.object_store.link_source", src)
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            _: ObjectStore,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, args, kwargs)

        wrap_function_wrapper(_OS_MODULE, "ObjectStore.link_object", decorator)

    def _instrument_update_metadata(self) -> None:
        tracer = self.tracer

        async def _wrapped(
            wrapper: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            if not is_instrumentation_enabled():
                return await wrapper(*args, **kwargs)
            name: str = args[0]
            span = (
                SpanBuilder(tracer, SpanKind.CLIENT, SpanAction.OBJ_UPDATE_METADATA)
                .with_object_name(name)
                .build()
            )
            with trace.use_span(span, end_on_exit=True):
                return await wrapper(*args, **kwargs)

        def decorator(
            wrapper: Any,
            _: ObjectStore,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any:
            return _wrapped(wrapper, args, kwargs)

        wrap_function_wrapper(_OS_MODULE, "ObjectStore.update_metadata", decorator)
