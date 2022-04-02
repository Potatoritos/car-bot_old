from typing import (
    Callable, Optional, Any, TYPE_CHECKING, get_type_hints, Awaitable, Union
)
import inspect
import asyncio
from enum import Enum

# import config
from .argument import Argument, FromChoices, InRange
from .check import Check, RequiresPermissions, GuildOnly, SpecificGuildOnly
from .enums import CommandType, OptionType
from .exception import CommandError, CogError, CarException
from .util import generate_repr
if TYPE_CHECKING:
    from .cog import Cog
    from .context import Context

__all__ = [
    'Command',
    'TextCommand',
    'SlashCommand',
    'text_command',
    'slash_command',
    'mixed_command',
    'slash_command_group'
]

class Command:
    def __init__(
        self,
        *,
        name: str,
        func: Callable[..., Awaitable[Any]],
        desc: Optional[str] = None,
        category: str = "Uncategorized",
        max_concurrency: Optional[int] = None,
        hidden: bool = False
    ):
        self.name = name
        self.func = func
        self.desc: str = desc or inspect.getdoc(func) or "No description"
        self.category = category
        self.max_concurrency = max_concurrency
        self.hidden = hidden

        self.guild_id: Optional[int] = None
        if hasattr(func, '_car_guild_id'):
            self.guild_id = func._car_guild_id # type: ignore[attr-defined]

        self.checks: list[Check] = []
        if hasattr(func, '_car_checks'):
            self.checks = func._car_checks # type: ignore[attr-defined]

        self.parent_cog: Optional['Cog'] = None # set by Cog
        self.concurrency: int = 0

        self.args: dict[str, Argument] = {}
        hints = get_type_hints(self.func, include_extras=True)

        for name, param in inspect.signature(func).parameters.items():
            if name == 'self' or name == 'ctx':
                continue
            self.args[name] = Argument.from_hint(hints[name], name=name,
                                                 default=param.default)

    def outline(self, *, ctx_args: dict[str, Any] = {}, prefix: str = "/",
                    highlight: Optional[str] = None) -> str:
        outline = ["``", prefix, self.name]

        for i, arg in enumerate(self.args.values()):
            label = str(ctx_args.get(arg.name, arg.label))
            if label == "":
                label = " "

            if highlight is not None and arg.name == highlight:
                label = f"``**__`{label}`__**"
                if i != len(self.args)-1:
                    label += "``"
            elif i == len(self.args)-1:
                label += '``'

            outline.append(" ")
            outline.append(label)

        if len(self.args) == 0:
            outline.append("``")

        return "".join(outline)

    def usage(self, *, prefix: str = "/") -> str:
        items: list[str] = []
        items.append(self.outline(prefix=prefix))

        for arg in self.args.values():
            items.append(arg.usage_label(slash=False))

        return "\n\n".join(items)

    def add_check(self, check: 'Check') -> None:
        self.checks.append(check)
        if isinstance(check, SpecificGuildOnly):
            self.guild_id = check.guild_id

    # raises CheckError if checks fail
    def run_checks(self, ctx: 'Context') -> None:
        for check in self.checks:
            check.check(ctx)

    # def run(self, ctx: 'Context') -> None:
        # try:
            # asyncio.create_task(self._run(ctx))
        # except Exception as e:
            # print(e)

    async def run(self, ctx: 'Context'):
        if self.max_concurrency is not None and \
                self.concurrency >= self.max_concurrency:
            raise CommandError("Maximum concurrency reached!")

        if self.parent_cog is None:
            raise CogError("This command has not been initialized properly!")

        self.concurrency += 1

        try:
            await self.func(self.parent_cog, ctx, **ctx.args)
        except CarException as e:
            self.concurrency -= 1
            raise e

        self.concurrency -= 1


class SlashCommand(Command):
    def __init__(
        self,
        *,
        name: str,
        func: Callable[..., Awaitable[Any]],
        desc: Optional[str] = None,
        category: str = "Uncategorized",
        max_concurrency: Optional[int] = None,
        hidden: bool = False,
    ):
        super().__init__(name=name, func=func, desc=desc, category=category,
                         max_concurrency=max_concurrency, hidden=hidden)
        self.parent_cog: 'Cog' # = None # set by CogHandler
        self.subcommands: list[SlashCommand] = [] # also set by CogHandler

    def __repr__(self) -> str:
        return generate_repr("SlashCommand", (
            ('name', self.name),
            ('category', self.category),
            ('desc', self.desc),
            ('max_concurrency', self.max_concurrency),
            ('hidden', self.hidden)
        ))

    def has_parent(self) -> bool:
        return self.name.find(' ') != -1

    @property
    def parent_name(self) -> str:
        idx = self.name.rfind(' ')
        assert idx != -1
        return self.name[:idx]

    @property
    def rightmost_name(self) -> str:
        return self.name[self.name.rfind(' ')+1:]

    def json(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            'name': self.rightmost_name,
            'description': self.desc
        }
        if self.has_parent():
            data['type'] = OptionType.SUB_COMMAND_GROUP
        else:
            if self.guild_id is not None:
                data['guild_id'] = self.guild_id

            data['type'] = CommandType.CHAT_INPUT
            # data['application_id'] = config.APPLICATION_ID

        data['options'] = []
        if len(self.subcommands) == 0:
            data['type'] = OptionType.SUB_COMMAND
            for arg in self.args.values():
                data['options'].append(arg.json())

        return data


class TextCommand(Command):
    def __init__(
        self,
        *,
        name: str,
        func: Callable[..., Awaitable[Any]],
        desc: Optional[str] = None,
        aliases: tuple[str, ...] = (),
        category: str = "Uncategorized",
        collect_last_arg: bool = False,
        max_concurrency: Optional[int] = None,
        hidden: bool = False
    ):
        super().__init__(name=name, func=func, desc=desc, category=category,
                         max_concurrency=max_concurrency, hidden=hidden)
        self.aliases = aliases
        self.collect_last_arg = collect_last_arg

    def __repr__(self) -> str: 
        return generate_repr("TextCommand", (
            ("name", self.name),
            ("category", self.category),
            ("desc", self.desc),
            ("aliases", self.aliases),
            ("max_concurrency", self.max_concurrency),
            ("collect_last_arg", self.collect_last_arg),
            ("hidden", self.hidden)
        ))


class MixedCommandContainer:
    def __init__(
        self,
        *,
        slash_command: SlashCommand,
        text_command: TextCommand
    ):
        self.slash_command = slash_command
        self.text_command = text_command

def mixed_command(*, text_name: Optional[str] = None,
                  slash_name: Optional[str] = None,
                  aliases: tuple[str, ...] = (), **kwargs):
    def decorator(func):
        return MixedCommandContainer(
            slash_command=SlashCommand(name=slash_name or func.__name__,
                                       func=func, **kwargs),
            text_command=TextCommand(name=text_name or func.__name__, func=func,
                                     aliases=aliases, **kwargs)
        )
    return decorator

def text_command(*, name: Optional[str] = None, **kwargs):
    def decorator(func):
        return TextCommand(name=name or func.__name__, func=func, **kwargs)
    return decorator

def slash_command(*, name: Optional[str] = None, **kwargs):
    def decorator(func):
        return SlashCommand(name=name or func.__name__, func=func, **kwargs)
    return decorator

def slash_command_group(*, name: str, desc: str = "Command Group"):
    def decorator(func):
        return SlashCommand(func=func, name=name, desc=desc, hidden=True)
    return decorator

