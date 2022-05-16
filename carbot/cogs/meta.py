import os
import time
from typing import Annotated as A, Optional, Union

import discord
import git
import psutil

import car


class Meta(car.Cog):
    category = "Meta"

    def cmdlist_embed(self, ctx: car.Context,
                      commands: Union[dict[str, car.SlashCommand],
                                      dict[str, car.TextCommand]],
                      sep: bool = False,
                      view_hidden: bool = False,
                      **embed_kwargs) -> discord.Embed:
        categories: dict[str, list[str]] = {}

        for name, cmd in sorted(commands.items()):
            if cmd.guild_id is not None and cmd.guild_id != ctx.guild.id:
                continue
            if cmd.hidden:
                if not view_hidden:
                    continue

                name = f"({name})"

            n = f"`{name}`"
            try:
                cmd.run_checks(ctx)
            except car.CheckError:
                n = f"~~`{name}`~~"

            if cmd.hidden:
                n = f"*{n}*"

            if cmd.category not in categories:
                categories[cmd.category] = []

            no_break_space = '\u00A0'
            categories[cmd.category].append(n.replace(' ', no_break_space))

        e = discord.Embed(**embed_kwargs)
        en_space = '\u2002'
        if sep:
            en_space = f",{en_space}"

        for name, cmds in sorted(categories.items()):
            e.add_field(
                name=name,
                value=en_space.join(cmds),
                inline=False
            )
        return e

    def cmdhelp_embed(self, ctx: car.Context, cmd: car.Command,
                      embed_title: str) -> discord.Embed:
        desc = cmd.desc
        e = discord.Embed(title=embed_title, description=cmd.desc)

        e.add_field(name="Usage", value=cmd.usage(prefix=ctx.prefix),
                    inline=False)

        if isinstance(cmd, car.SlashCommand) and len(cmd.subcommands) > 0:
            no_break_space = '\u00A0'
            en_space = '\u2002'

            e.add_field(name="Subcommands",
                        value=en_space.join(
                            f"`{c.name.replace(' ', no_break_space)}`"
                            for c in cmd.subcommands
                        ))

        if isinstance(cmd, car.TextCommand) and len(cmd.aliases) > 0:
            e.add_field(name="Aliases",
                        value=' '.join(f"`{a}`" for a in cmd.aliases),
                        inline=False)

        if len(cmd.checks) > 0:
            e.add_field(name="Checks",
                        value="This command:\n"
                        + '\n'.join(c.desc(ctx) for c in cmd.checks),
                        inline=False)
        return e

    @car.mixed_command(text_name="help", slash_name="help_text",
                       aliases=("help_text",))
    async def text_help(
        self,
        ctx: car.TextContext,
        command: A[
            Optional[str],
            ("the name of a text command; if unspecified, returns the text "
             "command list")
        ] = None,
        view_hidden: Optional[bool] = False
    ):
        """Views text command help / displays the usage of a text command"""
        if command is None:
            title = "Text Command List"
            desc = (
                f"Use `{ctx.prefix}syntax` to learn how to use text "
                "commands\n"
                f"Use `{ctx.prefix}help [command]` to view command usage\n"
                f"Use `/help` (or `{ctx.prefix}help_slash`) to view slash"
                " command help"
            )
            await ctx.respond(embed=self.cmdlist_embed(
                ctx, self.bot.cog_handler.text_commands,
                title=title, description=desc, view_hidden=view_hidden
            ))
            return

        cmd = self.bot.cog_handler.text_commands.get(command)
        if cmd is None:
            raise car.ArgumentError(f"Invalid command! Use `{ctx.prefix}help` "
                                "to view the list of commands.", 'command')

        await ctx.respond(embed=self.cmdhelp_embed(
                ctx, cmd, f"Text command: {cmd.name}"))


    @car.mixed_command(text_name="help_slash", slash_name="help")
    async def slash_help(
        self,
        ctx: car.SlashContext,
        command: A[
            Optional[str],
            ("the name of a slash command; if unspecified, returns the slash "
             "command list")
        ] = None,
        view_hidden: Optional[bool] = False
    ):
        """Views slash command help / displays the usage of a slash command"""
        if command is None:
            title = "Slash Command List"
            desc = (
                "Use `/help [command]` to view command usage\n"
                f"Use `/help_text` or `(insert alt help here)` to view "
                "the list of text commands"
            )
            await ctx.respond(embed=self.cmdlist_embed(
                ctx, self.bot.cog_handler.slash_commands,
                sep=True, title=title, description=desc,
                view_hidden=view_hidden
            ))
            return

        cmd = self.bot.cog_handler.slash_commands.get(command)
        if cmd is None:
            raise car.ArgumentError(f"Invalid command! Use `/help` to view the "
                                "list of commands.", 'command')

        await ctx.respond(embed=self.cmdhelp_embed(
                ctx, cmd, f"Slash command: {cmd.name}"))

    @car.mixed_command()
    async def syntax(self, ctx: car.Context):
        """Displays text command syntax help"""
        await ctx.respond("WIP")

    @car.mixed_command()
    async def ping(self, ctx: car.TextContext):
        """Displays my latency"""
        p = f":heart: {int(self.bot.latency*1000)}ms"
        e = discord.Embed(description=p)

        bef = time.monotonic()
        await ctx.respond("Pong!", embed=e)

        delta = time.monotonic() - bef
        p += f"\n:envelope: {int(delta*1000)}ms"

        await ctx.edit_response(embed=discord.Embed(description=p))

    @car.mixed_command()
    async def info(self, ctx):
        """Views bot technical info"""
        e = discord.Embed(title="Info")

        repo = git.Repo(search_parent_directories=True)
        sha = repo.head.object.hexsha

        commit_link = f"https://github.com/Potatoritos/car-bot/commit/{sha}"

        e.description = (
            f"Running [carbot](https://github.com/potatoritos/car-bot) "
            f"on commit [`{sha[:7]}`]({commit_link})"
        )
        mem_mb = psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2
        e.add_field(name="Memory usage", value=f"{mem_mb:.2f}MB")
        await ctx.respond(embed=e)

