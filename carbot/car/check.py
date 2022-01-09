from abc import ABCMeta, abstractmethod
from types import FunctionType
from typing import Any, Awaitable, Callable, Optional, TYPE_CHECKING, Union
import discord
from loguru import logger

from .exception import CheckError, ContextError
if TYPE_CHECKING:
    from .command import Command
    from .context import Context


__all__ = [
    'Check',
    'RequiresPermissions',
    'GuildOnly',
    'SpecificGuildOnly',
    'add_check',
    'requires_permissions',
    'guild_only',
    'guild_must_be_id'
]


class Check(metaclass=ABCMeta):
    EMOTE_YES = "`[✓]`"
    EMOTE_NO = "`[ ]`"

    def emote(self, condition) -> str:
        return self.EMOTE_YES if condition else self.EMOTE_NO

    # Raises CheckError if check fails
    @abstractmethod
    def check(self, ctx: 'Context') -> None:
        pass

    @abstractmethod
    def desc(self, ctx: 'Context') -> str:
        pass

    def modify_func(self, func: Callable[..., Awaitable[Any]]) -> None:
        pass


class RequiresPermissions(Check):
    def __init__(self, permissions: dict[str, bool]):
        self.permissions = permissions

    def get_missing(self, ctx: 'Context') -> list[str]:
        if isinstance(ctx.channel, discord.PartialMessageable):
            logger.error(
                f"Non-guild-only command requires permissions ({ctx})")
            raise ContextError(
                "Non-guild-only command cannot require permissions")
        perms = ctx.channel.permissions_for(ctx.author)

        return [
            p for p, v in self.permissions.items() if getattr(perms, p) != v
        ]

    def check(self, ctx: 'Context') -> None:
        missing = self.get_missing(ctx)
        if missing:
            raise CheckError("You aren't allowed to use this command!\n\n"
                             "Missing permissions:\n"
                             + '\n'.join(f"`{perm}`" for perm in missing))

    def desc(self, ctx: 'Context') -> str:
        missing = self.get_missing(ctx)
        return (
            f"{self.emote(len(missing) == 0)} requires permissions: "
            + ', '.join((p + (" (missing)" if p in missing else ""))
                        for p in self.permissions)
        )


class GuildOnly(Check):
    def check(self, ctx: 'Context') -> None:
        if ctx.is_dm():
            raise CheckError("This command is only available in servers!")

    def desc(self, ctx: 'Context') -> str:
        return f"{self.emote(not ctx.is_dm())} Must be used in a server"


class SpecificGuildOnly(Check):
    def __init__(self, guild_id: int):
        self.guild_id = guild_id

    def check(self, ctx: 'Context') -> None:
        if ctx.is_dm():
            raise CheckError("This command is only available in servers!")
        elif ctx.guild.id != self.guild_id:
            raise CheckError("This command is not available in this server!")

    def desc(self, ctx: 'Context') -> str:
        if ctx.is_dm() or ctx.guild.id != self.guild_id:
            return f"{self.EMOTE_NO} is not available in this server"
        else:
            return f"{self.EMOTE_YES} is available in this server"

    def modify_func(self, func: Callable[..., Awaitable[Any]]):
        func._car_guild_id = self.guild_id # type: ignore[attr-defined]

#TODO: annotate properly
def add_check(check: Check) -> Callable:
    def decorator(func: Optional[Callable[..., Awaitable[Any]]] = None):
        if func is not None:
            if not hasattr(func, '_car_checks'):
                func._car_checks = [] # type: ignore[attr-defined]
            func._car_checks.append(check) # type: ignore[attr-defined]
            check.modify_func(func)
            return func
        else: # if obj is a Command
            return check
    return decorator

def requires_permissions(**permissions) -> Callable:
    return add_check(RequiresPermissions(permissions))

def guild_only() -> Callable:
    return add_check(GuildOnly())

def guild_must_be_id(guild_id: int) -> Callable:
    return add_check(SpecificGuildOnly(guild_id))

