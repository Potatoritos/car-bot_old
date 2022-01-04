from typing import Any
import discord
from loguru import logger

from carpp import fuzzy_match_one
from .argument import Argument
from .context import Context
from .exception import ArgumentError, CheckError
from .util import join_last

__all__ = [
    'convert',
]


def conv_int(arg: Argument, ctx: Context, val: str) -> int:
    try:
        res = int(val)
    except ValueError:
        raise ArgumentError("This argument must be an integer!")

    if arg.min_value is not None and arg.max_value is not None \
            and not arg.min_value <= res <= arg.max_value:
        raise ArgumentError(f"This number must be at least {arg.min_value} and"
                            f" at most {arg.max_value}!")
    if arg.min_value is not None and res < arg.min_value:
        raise ArgumentError(f"This number must be at least {arg.min_value}!")
    if arg.max_value is not None and res > arg.max_value:
        raise ArgumentError(f"This number must be at most {arg.max_value}")

    if arg.choices is not None and res not in arg.choices:
        raise ArgumentError("This number must be one of the following: "
                            + join_last([f"`{c}`" for c in arg.choices], "or"))

    return res

def conv_float(arg: Argument, ctx: Context, val: str) -> float:
    try:
        res = float(val)
    except ValueError:
        spl = val.split('/')
        print(spl)
        if len(spl) == 2:
            try:
                res = float(spl[0]) / float(spl[1])
            except ZeroDivisionError:
                raise ArgumentError("I can't divide by zero!")
            except ValueError:
                raise ArgumentError("Invalid fraction! (fractions must be in "
                                    "the form a/b, where a and b are numbers)")
        else:
            raise ArgumentError("This must be a number!")

    if arg.min_value is not None and arg.max_value is not None \
            and not arg.min_value <= res <= arg.max_value:
        raise ArgumentError(f"This number must be at least {arg.min_value} and"
                            f" at most {arg.max_value}!")
    if arg.min_value is not None and res < arg.min_value:
        raise ArgumentError(f"This number must be at least {arg.min_value}!")
    if arg.max_value is not None and res > arg.max_value:
        raise ArgumentError(f"This number must be at most {arg.max_value}")

    if arg.choices is not None and res not in arg.choices:
        raise ArgumentError("This number must be one of the following: "
                            + join_last([f"`{c}`" for c in arg.choices], "or"))

    return res

def conv_str(arg: Argument, ctx: Context, val: str) -> str:
    if arg.choices is not None and val not in arg.choices:
        raise ArgumentError("This must be one of the following: "
                            + join_last([f"`{c}`" for c in arg.choices], "or"))
    return val

def conv_bool(arg: Argument, ctx: Context, val: str) -> bool:
    true_vals = ("true", "1")
    false_vals = ("false", "0")
    lower = val.lower()
    if lower.startswith("y") or lower in true_vals:
        return True
    if lower.startswith("n") or lower in false_vals:
        return False

    raise ArgumentError("This must be `yes` or `no`! (alternatively: "
                        "`true`/`false`, `1`/`0`, or `y`/`n`)")

def conv_member(arg: Argument, ctx: Context, val: str) -> discord.Member:
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
        members = [m for m in ctx.guild.members if m.discriminator == discrim]

    dist1, idx1 = fuzzy_match_one(val, [m.name for m in members])

    members_nick = [m for m in members if m.nick is not None]
    dist2, idx2 = fuzzy_match_one(val, [m.nick for m in members_nick
                                        if m.nick is not None]) # for mypy

    return members[idx1] if dist1 <= dist2 else members_nick[idx2]

def conv_role(arg: Argument, ctx: Context, val: str) -> discord.Role:
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

def conv_text_channel(arg: Argument, ctx: Context, val: str
                      ) -> discord.TextChannel:
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

converters = {
    int: conv_int,
    str: conv_str,
    bool: conv_bool,
    float: conv_float,
    discord.Member: conv_member,
    discord.Role: conv_role,
    discord.TextChannel: conv_text_channel
}

def convert(arg: Argument, ctx: Context, val: str) -> Any:
    return converters[arg.arg_type](arg, ctx, val)

