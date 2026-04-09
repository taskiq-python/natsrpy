from collections.abc import Callable
from typing import Any, Concatenate

from typing_extensions import ParamSpec
from wrapt import ObjectProxy

_P = ParamSpec("_P")


class AsyncCtxManagerProxy(ObjectProxy):  # type: ignore
    """
    Proxy object for context managers.

    This class wraps a context manager,
    wrapping returned values on __aenter__,
    and calling __cancel_ctx__ at the exit.
    """

    def __init__(
        self,
        wrapped: Any,
        sub_wrappers: dict[type[Any], Callable[Concatenate[Any, _P], Any]],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> None:
        super().__init__(wrapped)
        self._self_sub_args = args
        self._self_sub_kwargs = kwargs
        self._self_sub = None
        self._self_subwrappers = sub_wrappers

    async def __aenter__(self) -> Any:
        sub: Any = await self.__wrapped__.__aenter__()
        sub_wrapper = self._self_subwrappers.get(type(sub))
        if sub_wrapper:
            sub = sub_wrapper(sub, *self._self_sub_args, **self._self_sub_kwargs)
        self._self_sub = sub
        return sub

    async def __aexit__(self, *args: object, **kwargs: dict[Any, Any]) -> Any:
        if self._self_sub and hasattr(self._self_sub, "__cancel_ctx__"):
            self._self_sub.__cancel_ctx__(*args, **kwargs)
