import asyncio
from typing import Any, Type, Union, TYPE_CHECKING
import json
import requests
import discord
from loguru import logger

import config
from .cog import Cog
from .command import Command, TextCommand, SlashCommand
from .context import Context, SlashContext, TextContext
from .converter import convert
from .exception import (
    CogError, CheckError, CommandError, ArgumentError, CarException
)
from .listener import Listener
from .tokenizer import Tokenizer, filter_kwargs
if TYPE_CHECKING:
    from .bot import Bot

__all__ = [
    'CogHandler'
]


class CogHandler:
    def __init__(self, bot: 'Bot'):
        self.cog_classes: dict[str, Type[Cog]] = {}
        self.cogs: dict[str, Cog] = {}
        self.slash_commands: dict[str, SlashCommand] = {}
        self.text_commands: dict[str, TextCommand] = {}
        self.text_aliases: dict[str, TextCommand] = {}
        self.listeners: dict[str, dict[str, Listener]] = {}

        self.bot = bot

    def add_cog_class(self, cog: Type[Cog]) -> None:
        if cog.__name__ in self.cog_classes:
            raise CogError(f"Duplicate cog class name: {cog.__name__}")

        self.cog_classes[cog.__name__] = cog

    def remove_cog_class(self, cog_name: str) -> None:
        del self.cog_classes[cog_name]

    def load_cog(self, cog_name: str) -> None:
        logger.info(f"Loading cog '{cog_name}'")
        if cog_name in self.cogs:
            raise CogError(f"Cog {cog_name} is already loaded!")

        self.cogs[cog_name] = self.cog_classes[cog_name](self.bot)

        for text_cmd in self.cogs[cog_name].text_commands:
            self._load_text_command(text_cmd)
        for slash_cmd in self.cogs[cog_name].slash_commands:
            self._load_slash_command(slash_cmd)

        for listener in self.cogs[cog_name].listeners:
            self._load_listener(cog_name, listener)

    def unload_cog(self, cog_name: str) -> None:
        for text_cmd in self.cogs[cog_name].text_commands:
            self._unload_text_command(text_cmd.name)
        for slash_cmd in self.cogs[cog_name].slash_commands:
            self._unload_slash_command(slash_cmd.name)

        self._unload_listeners(cog_name)

        del self.cogs[cog_name]

    def reload_cog(self, cog_name: str) -> None:
        self.unload_cog(cog_name)
        self.load_cog(cog_name)

    def _load_text_command(self, cmd: TextCommand) -> None:
        if cmd.name in self.text_commands or cmd.name in self.text_aliases:
            raise CogError(f"Duplicate command name! {cmd}")

        self.text_commands[cmd.name] = cmd
        for alias in cmd.aliases:
            if alias in self.text_commands or alias in self.text_aliases:
                raise CogError(f"Duplicate command name! {cmd}")
            self.text_aliases[alias] = cmd 

    def _unload_text_command(self, cmd_name: str) -> None:
        for alias in self.text_commands[cmd_name].aliases:
            del self.text_aliases[alias]
        del self.text_commands[cmd_name]

    def _load_slash_command(self, cmd: SlashCommand) -> None:
        if cmd.name in self.slash_commands:
            raise CogError(f"Duplicate command name! {cmd}")
        self.slash_commands[cmd.name] = cmd

        if cmd.has_parent():
            self.slash_commands[cmd.parent_name].subcommands.append(cmd)

    def _unload_slash_command(self, cmd_name: str) -> None:
        del self.slash_commands[cmd_name]

    def _load_listener(self, cog_name: str, listener: Listener) -> None:
        if listener.event not in self.listeners:
            self.listeners[listener.event] = {}
        self.listeners[listener.event][cog_name] = listener

    def _unload_listeners(self, cog_name: str) -> None:
        for dct in self.listeners.values():
            if cog_name in dct:
                del dct[cog_name]

    def slash_commands_json(self) -> list[dict]:
        cmd_list: list[dict] = []

        def recurse(cmd: SlashCommand, parent_options: list[dict]) -> None:
            data = cmd.json()

            for subcmd in cmd.subcommands:
                recurse(subcmd, data["options"])

            parent_options.append(data)

        for cmd in self.slash_commands.values():
            if not cmd.has_parent():
                recurse(cmd, cmd_list)

        logger.debug(json.dumps(cmd_list, indent=4))
        return cmd_list

    def put_slash_commands(self) -> None:
        cmd_list = self.slash_commands_json()
        GUILD_ID = 495327409487478785
        
        url = ("https://discord.com/api/v8/applications/"
               f"{config.APPLICATION_ID}/guilds/{GUILD_ID}/commands")
        headers = {"Authorization": f"Bot {config.TOKEN}"}

        logger.info("Sending slash command list to discord...")
        r = requests.put(url, headers=headers, json=cmd_list)

        if r.status_code != 200:
            logger.error(f"Slash command registration failed (Status code "
                         f"{r.status_code}): {json.dumps(r.json(), indent=4)}")
        else:
            logger.success("Slash commands registered!")
            logger.debug(json.dumps(r.json(), indent=4))

    async def handle_error(self, ctx: Context, cmd: Command, e: CarException
                           ) -> None:
        if isinstance(e, CheckError) or isinstance(e, CommandError):
            desc = f":x: {e.error_msg}"

        elif isinstance(e, ArgumentError):
            outline = cmd.outline(ctx_args=ctx.args, prefix=ctx.prefix,
                                  highlight=e.highlight)
            desc = f":x: {outline}\n\n{e.error_msg}\n\nCorrect usage:\n" \
                    + cmd.usage(prefix=ctx.prefix)

        else:
            desc = f":x: An unknown error occured!"
            logger.error(f"Error when running command {cmd} ({ctx}):")
            logger.error(e)

        embed = discord.Embed(description=desc)

        if isinstance(ctx, TextContext) or (isinstance(ctx, SlashContext) \
                and not ctx.interaction.response.is_done()):
            await ctx.respond(embed=embed)
        else:
            await ctx.send(embed=embed)

    async def run_command_slash(self, ctx: SlashContext, data: dict[str, Any]
                                ) -> None:
        names: list[str] = []
        options: list[dict] = []

        while data['type'] == 1 or data['type'] == 2:
            names.append(data['name'])
            if 'options' not in data:
                break
            options = data['options']
            data = data['options'][0]

        name = ' '.join(names)
        cmd = self.slash_commands.get(name)
        if cmd is None:
            logger.error(f"Slash command '{name}' not recognized (probably "
                         "because discord hasn't updated the command list yet")
            return

        try:
            cmd.run_checks(ctx)
        except CheckError as e:
            await self.handle_error(ctx, cmd, e)
            return

        args: dict[str, Any] = {opt['name']: opt['value'] for opt in options
                                if 'value' in opt}
        try:
            for arg in cmd.args.values():
                if arg.name not in args:
                    if arg.required:
                        raise ArgumentError("I am missing this argument!",
                                            arg.name)
                        break
                    else:
                        continue
                try:
                    ctx.args[arg.name] = args[arg.name]
                    if not isinstance(ctx.args[arg.name], arg.arg_type):
                        ctx.args[arg.name] = convert(arg, ctx, args[arg.name])
                except ArgumentError as e:
                    logger.error(f"Slash command {cmd} ({ctx}) has invalid "
                                 "arguments (probably because discord hasn't"
                                 "updated the command list yet)")
                    return

            await cmd.run(ctx)
        except CarException as e:
            await self.handle_error(ctx, cmd, e)

    async def run_command_text(self, ctx: TextContext, cmd: TextCommand,
                               content: str) -> None:
        try:
            cmd.run_checks(ctx)
        except CheckError as e:
            await self.handle_error(ctx, cmd, e)
            return

        try:
            content, kwargs = filter_kwargs(content)
            tok = Tokenizer(content)

            for i, arg in enumerate(cmd.args.values()):
                if arg.name in kwargs:
                    ctx.args[arg.name] = kwargs[arg.name]
                else:
                    if tok.is_eof():
                        if arg.required:
                            raise ArgumentError("I am missing this argument!",
                                                arg.name)
                        else:
                            continue

                    if cmd.collect_last_arg and i == len(cmd.args)-1:
                        ctx.args[arg.name] = tok.get_remaining()
                    else:
                        ctx.args[arg.name] = tok.next_token()
                try:
                    ctx.args[arg.name] = convert(arg, ctx, ctx.args[arg.name])
                except ArgumentError as e:
                    e.highlight = arg.name
                    raise e

            await cmd.run(ctx)
        except CarException as e:
            await self.handle_error(ctx, cmd, e)

    def run_listeners(self, event: str, args: tuple[Any, ...],
                      kwargs: dict[str, Any]):
        if event not in self.listeners:
            return
        for listener in self.listeners[event].values():
            asyncio.create_task(listener.run(args, kwargs))

