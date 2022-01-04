from types import FunctionType
from .exception import CheckError


__all__ = [
    'check',
    'requires_permissions',
    'guild_only',
    'guild_must_be_id'
]

def check(condition):
    def decorator(func):
        if isinstance(func, FunctionType):
            if not hasattr(func, '_car_command_checks'):
                func._car_command_checks = [] # type: ignore[attr-defined]
            func._car_command_checks.append(condition) # type: ignore[attr-defined]
        else:
            func.checks.append(condition)
        return func
    return decorator

def requires_permissions(**permissions):
    def condition(ctx):
        perms = ctx.channel.permissions_for(ctx.author)
        missing = [
            p for p, v in permissions.items() if getattr(perms, p) != v
        ]
        if missing:
            raise CheckError("You aren't allowed to use this command!\n\n"
                             "Missing permissions:\n"
                             + '\n'.join(f"`{perm}`" for perm in missing))
    return check(condition)

def guild_only():
    def condition(ctx):
        if ctx.guild is None:
            raise CheckError("This command is not available in DMs!")
    return check(condition)

def guild_must_be_id(guild_id: int):
    def condition(ctx):
        if ctx.guild is None:
            raise CheckError("This command is not available in DMs!")

        elif ctx.guild.id != guild_id:
            raise CheckError("This command is not available in this server!")

    def decorator(func):
        if isinstance(func, FunctionType):
            if not hasattr(func, '_car_command_checks'):
                func._car_command_checks = [] # type: ignore[attr-defined]
            func._car_command_checks.append(condition) # type: ignore[attr-defined]
            func._car_required_guild = guild_id # type: ignore[attr-defined]
        else:
            func.checks.append(condition)
            func.required_guild = guild_id
        return func

    return decorator

