from abc import ABC, abstractmethod
import time
from typing import Any, Optional
import urllib.parse

import discord
from loguru import logger

from carpp import fuzzy_match_one
from .context import Context
from .enums import OptionType, ChannelType
from .exception import ArgumentError, CheckError
from .util import join_last


__all__ = [
    'Converter',
    'JoinedConverter',
    'FromChoices',
    'InRange',
    'ToInt',
    'ToFloat',
    'ToString',
    'ToSeconds',
    'ToURL',
    'ToBool',
    'ToMember',
    'ToRole',
    'ToVoiceChannel',
    'ToTextChannel',
    'ToEmote',
    'default_converters'
]

# class CanConvert(Protocol):
    # async def convert(self, ctx: Context, val: str)  ->  Any:
        # ...

class Converter(ABC):
    def __or__(self, other: 'Converter'):
        return JoinedConverter() | self | other

    @abstractmethod
    async def convert(self, ctx: Context, val: Any) -> Any:
        pass

    async def convert_slash(self, ctx: Context, val: Any) -> Any:
        return await self.convert(ctx, val)

    @abstractmethod
    def modify_slash_data(self, data: dict[str, Any]) -> None:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    def slash_description(self) -> str:
        return self.description


class JoinedConverter(Converter):
    def __init__(self):
        self.converters = []

    def __or__(self, other: Converter):
        self.converters.append(other)
        return self

    async def convert(self, ctx: Context, val: str) -> Any:
        for converter in self.converters:
            val = await converter.convert(ctx, val)
        return val

    def modify_slash_data(self, data: dict[str, Any]) -> None:
        for converter in self.converters:
            converter.modify_slash_data(data)

    @property
    def description(self) -> str:
        return ' '.join(converter.description for converter in self.converters)


class FromChoices(Converter):
    def __init__(
        self,
        choices: dict[str, int] | dict[str, float] | dict[str, str],
    ):
        assert len(choices) > 0
        self.choices = choices

    async def convert(self, ctx: Context, val: str) -> Any:
        if val not in self.choices:
            raise ArgumentError(f"This argument must be {self.description}")

        return self.choices[val]

    async def convert_slash(self, ctx: Context, val: Any) -> Any:
        if val not in self.choices.values():
            raise ArgumentError("Invalid choice! (probably because slash "
                                "command list not updated)")
        return val

    def modify_slash_data(self, data: dict[str, Any]) -> None:
        data['type'] = {
            int: OptionType.INTEGER,
            float: OptionType.NUMBER,
            str: OptionType.STRING
        }[type(next(iter(self.choices.values())))]

        data['choices'] = [{'name': name, 'value': val}
                           for name, val in self.choices.items()]

    @property
    def description(self) -> str:
        return join_last([f"`{name}`" for name in self.choices], 'or')

    @property
    def slash_description(self) -> str:
        return "from the list of choices"


class InRange(Converter):
    def __init__(
        self,
        lower: Optional[int | float] = None,
        upper: Optional[int | float] = None
    ):
        self.lower = lower
        self.upper = upper

        assert lower is not None or upper is not None

    async def convert(self, ctx: Context, val: int | float) -> int | float:
        if self.lower is not None and self.upper is not None \
                and not self.lower <= val <= self.upper:
            raise ArgumentError(f"This number must ≥ {self.lower} "
                                f"and ≤ {self.upper}!")
        elif self.lower is not None and val < self.lower:
            raise ArgumentError(f"This number must be ≥ {self.lower}!")
        elif self.upper is not None and val > self.upper:
            raise ArgumentError(f"This number must be ≤ {self.upper}")

        return val

    def modify_slash_data(self, data: dict[str, Any]) -> None:
        data['min_value'] = self.lower
        data['max_value'] = self.upper

    @property
    def description(self) -> str:
        desc = []
        if self.lower is not None:
            desc.append(f"≥ {self.lower}")
        if self.upper is not None:
            desc.append(f"≤ {self.upper}")

        return " and ".join(desc)


class ToInt(Converter):
    async def convert(self, ctx: Context, val: str) -> int:
        try:
            return int(val)
        except ValueError:
            raise ArgumentError(f"This argument must be {self.description}!")

    def modify_slash_data(self, data: dict[str, Any]) -> None:
        data['type'] = OptionType.INTEGER

    @property
    def description(self) -> str:
        return "an integer"


class ToFloat(Converter):
    async def convert(self, ctx: Context, val: str) -> float:
        try:
            return float(val)
        except ValueError:
            spl = val.split('/')
            if len(spl) == 2:
                try:
                    return float(spl[0]) / float(spl[1])
                except ZeroDivisionError:
                    raise ArgumentError("I can't divide by zero!")
                except ValueError:
                    raise ArgumentError("Invalid fraction! (fractions must be "
                                        "in the form a/b, where a and b are "
                                        "numbers)")
            else:
                raise ArgumentError("This must be a number!")

    def modify_slash_data(self, data: dict[str, Any]) -> None:
        data['type'] = OptionType.NUMBER

    @property
    def description(self) -> str:
        return "a number"


class ToString(Converter):
    async def convert(self, ctx: Context, val: str) -> str:
        return val

    def modify_slash_data(self, data: dict[str, Any]) -> None:
        data['type'] = OptionType.STRING

    @property
    def description(self) -> str:
        return "a string"


class ToSeconds(Converter):
    def __init__(self, allow_negative: bool = False):
        self.allow_negative = allow_negative

    async def convert(self, ctx: Context, val: str) -> float:
        try:
            return float(val)
        except ValueError:
            spl = val.split(':')
            res = 0

            try:
                match len(spl):
                    case 2:
                        res = 60*float(spl[0]) + float(spl[1])
                    case 3:
                        res = 3600*int(spl[0]) + 60*float(spl[1]) \
                            + float(spl[2])
                    case _:
                        raise ValueError
                        
            except ValueError:
                raise ArgumentError(f"This argument must be {self.description}!")

            if res < 0 and not self.allow_negative:
                raise ArgumentError(f"This timestamp must be positive!")

            return res

    def modify_slash_data(self, data: dict[str, Any]) -> None:
        data['type'] = OptionType.STRING

    @property
    def description(self) -> str:
        return "a timestamp/duration (in seconds or HH:MM:SS.ms)"


class ToURL(Converter):
    def __init__(self, allowed_sites: Optional[set[str]]=None):
        self.allowed_sites = allowed_sites

    async def convert(self, ctx: Context, val: str) -> str:
        symbols = set(".-_~:/?#[]@!$&'()*+,;%=")
        print(f"{val=}")
        if not all('a' <= c <= 'z' or 'A' <= c <= 'Z' \
                   or '0' <= c <= '9' or c in symbols for c in val) \
                or not '.' in val:
            raise ArgumentError("Invalid URL!")

        if not val.startswith('http'):
            val = f"https://{val}"

        netloc = urllib.parse.urlparse(val).netloc
        if netloc.startswith('www.'):
            netloc = netloc[4:]

        if netloc == '':
            raise ArgumentError("Invalid URL!")

        if self.allowed_sites is not None and netloc not in self.allowed_sites:
            raise ArgumentError("Disallowed site!")

        return val

    def modify_slash_data(self, data: dict[str, Any]) -> None:
        data['type'] = OptionType.STRING

    @property
    def description(self) -> str:
        return "a URL"


class ToBool(Converter):
    async def convert(self, ctx: Context, val: str) -> bool:
        true_vals = ('true', '1')
        false_vals = ('false', '0')
        lower = val.lower()

        if lower.startswith('y') or lower in true_vals:
            return True
        if lower.startswith('n') or lower in false_vals:
            return False

        raise ArgumentError("This must be `yes` or `no`! (alternatively: "
                        "`true`/`false`, `1`/`0`, or `y`/`n`)")

    def modify_slash_data(self, data: dict[str, Any]) -> None:
        data['type'] = OptionType.STRING
        data['choices'] = [
            {'name': 'Yes', 'value': '1'},
            {'name': 'No', 'value': '0'}
        ]

    @property
    def description(self) -> str:
        return "`yes` or `no`"


class ToMember(Converter):
    async def convert(self, ctx: Context, val: str) -> discord.Member:
        if ctx.guild is None:
            logger.warning("Non-DM Argument found in non-guild-only command!")
            raise CheckError("You must be in a server to use this command!")

        member_id = None
        try:
            member_id = int(val)
        except ValueError:
            pass
        if val.startswith('<@') and val.endswith('>'):
            try:
                member_id = int(val[(3 if val.startswith('<@!') else 2) : -1])
            except ValueError:
                pass
        if member_id is not None:
            m = discord.utils.get(ctx.guild.members, id=int(member_id))
            if m is not None:
                return m

        discrim = None
        if len(val) > 5 and val[-5] == '#':
            try:
                int(val[-4:])
                discrim = val[-4:]
            except ValueError:
                pass

        if discrim is None:
            members = ctx.guild.members
        else:
            members = [m for m in ctx.guild.members
                       if m.discriminator == discrim]

        dist1, idx1 = fuzzy_match_one(val, [m.name for m in members])

        members_nick = [m for m in members if m.nick is not None]
        dist2, idx2 = fuzzy_match_one(val.lower(),
                                      [m.nick.lower() for m in members_nick
                                       if m.nick is not None]) # for mypy

        return members[idx1] if dist1 <= dist2 else members_nick[idx2]

    def modify_slash_data(self, data: dict[str, Any]) -> None:
        data['type'] = OptionType.USER

    @property
    def description(self) -> str:
        return "a member"


class ToRole(Converter):
    async def convert(self, ctx: Context, val: str) -> discord.Role:
        if ctx.guild is None:
            logger.warning("Non-DM Argument found in non-guild-only command!")
            raise CheckError("You must be in a server to use this command!")

        role_id = None
        try:
            role_id = int(val)
        except ValueError:
            pass
        if val.startswith('<@&') and val.endswith('>'):
            try:
                role_id = int(val[3:-1])
            except ValueError:
                pass
        if role_id is not None:
            r = discord.utils.get(ctx.guild.roles, id=role_id)
            if r is not None:
                return r

        _, idx = fuzzy_match_one(val, [r.name for r in ctx.guild.roles])
        return ctx.guild.roles[idx]

    def modify_slash_data(self, data: dict[str, Any]) -> None:
        data['type'] = OptionType.ROLE

    @property
    def description(self) -> str:
        return "a role"


class ToTextChannel(Converter):
    async def convert(self, ctx: Context, val: str) -> discord.TextChannel:
        if ctx.guild is None:
            logger.warning("Non-DM Argument found in non-guild-only command!")
            raise CheckError("You must be in a server to use this command!")

        channel_id = None
        try:
            channel_id = int(val)
        except ValueError:
            pass
        if val.startswith('<#') and val.endswith('>'):
            try:
                channel_id = int(val[2:-1])
            except ValueError:
                pass
        if channel_id is not None:
            c = discord.utils.get(ctx.guild.text_channels, id=channel_id)
            if c is not None:
                return c

        _, idx = fuzzy_match_one(val, [c.name for c in ctx.guild.text_channels])
        return ctx.guild.text_channels[idx]

    def modify_slash_data(self, data: dict[str, Any]) -> None:
        data['type'] = OptionType.CHANNEL
        data['channel_types'] = [ChannelType.GUILD_TEXT]

    @property
    def description(self) -> str:
        return "a text channel"


class ToVoiceChannel(Converter):
    async def convert(self, ctx: Context, val: str) -> discord.VoiceChannel:
        if ctx.guild is None:
            logger.warning("Non-DM Argument found in non-guild-only command!")
            raise CheckError("You must be in a server to use this command!")

        channel_id = None
        try:
            channel_id = int(val)
        except ValueError:
            pass
        if val.startswith('<#') and val.endswith('>'):
            try:
                channel_id = int(val[2:-1])
            except ValueError:
                pass
        if channel_id is not None:
            c = discord.utils.get(ctx.guild.voice_channels, id=channel_id)
            if c is not None:
                return c

        _, idx = fuzzy_match_one(val, [c.name for c in ctx.guild.voice_channels])
        return ctx.guild.voice_channels[idx]

    def modify_slash_data(self, data: dict[str, Any]) -> None:
        data['type'] = OptionType.CHANNEL
        data['channel_types'] = [ChannelType.GUILD_VOICE]

    @property
    def description(self) -> str:
        return "a voice channel"


class ToEmote(Converter):
    async def convert(self, ctx: Context, val: str) -> discord.Emoji:
        if val.startswith('<:') and val.endswith('>'):
            try:
                val = int(val.split(':')[-1][:-1])
            except ValueError:
                pass

        try:
            e = discord.utils.get(ctx.guild.emojis, id=int(val))
            if e is not None:
                return e
        except ValueError:
            pass

        e = discord.utils.get(ctx.guild.emojis, name=val)
        if e is not None:
            return e

        _, idx = fuzzy_match_one(val, [e.name for e in ctx.guild.emojis])
        return ctx.guild.emojis[idx]

    def modify_slash_data(self, data: dict[str, Any]) -> None:
        data['type'] = OptionType.STRING

    @property
    def description(self) -> str:
        return "an emote"

default_converters = {
    int: ToInt(),
    str: ToString(),
    bool: ToBool(),
    float: ToFloat(),
    discord.Member: ToMember(),
    discord.Role: ToRole(),
    discord.TextChannel: ToTextChannel(),
    discord.VoiceChannel: ToVoiceChannel(),
    discord.Emoji: ToEmote()
}

# async def convert(ctx: Context, val: str, convert_to: Type[Any]) -> Any:
    # return await converters[convert_to].convert(ctx, val)

# async def convert_arg(arg: Argument, ctx: Context, val: str) -> Any:
    # return await converters[arg.arg_type].convert_arg(arg, ctx, val)

