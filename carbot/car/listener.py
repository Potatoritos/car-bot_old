from typing import Callable, Awaitable, Any, TYPE_CHECKING, Optional

from .exception import CogError
if TYPE_CHECKING:
    from .cog import Cog

__all__ = [
    'Listener',
    'listener'
]


class Listener:
    def __init__(self, event: str, func: Callable[..., Awaitable[Any]]):
        self.event = event
        self.func = func
        self.parent: Optional['Cog'] = None # set by Cog

    async def run(self, args: tuple[Any, ...], kwargs: dict[str, Any]):
        if self.parent is None:
            raise CogError("This listener was not initialized properly")
        await self.func(self.parent, *args, **kwargs)

def listener(func):
    return Listener(func.__name__, func)

