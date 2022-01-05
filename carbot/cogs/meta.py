import discord
from typing import Annotated as A, Optional, Union
import car


class Meta(car.Cog):
    global_category = "Meta"

    async def cmdlist_embed(self,
                            ctx: car.Context,
                            commands: Union[dict[str, car.SlashCommand],
                                            dict[str, car.TextCommand]],
                            sep: bool = False,
                            **embed_kwargs) -> discord.Embed:
        categories: dict[str, list[str]] = {}

        for name, cmd in sorted(commands.items()):
            if cmd.guild_id is not None and cmd.guild_id != ctx.guild.id:
                continue
            if cmd.hidden:
                continue

            n = f"`{name}`"
            try:
                await cmd.run_checks(ctx)
            except car.CheckError:
                n = f"~~`{name}`~~"

            if cmd.category not in categories:
                categories[cmd.category] = []

            no_break_space = '\u00A0'
            categories[cmd.category].append(n.replace(' ', no_break_space))

        e = discord.Embed(**embed_kwargs)
        en_space = '\u2002'

        if sep:
            en_space = f",{en_space}"

        for name, cmds in categories.items():
            e.add_field(
                name=name,
                value=en_space.join(cmds),
                inline=False
            )

        return e

    async def cmdhelp_embed(self, ctx: car.Context, cmd: car.Command,
                            embed_title: str) -> discord.Embed:
        desc = cmd.desc
        e = discord.Embed(title=embed_title, description=cmd.desc)

        e.add_field(name="Usage", value=cmd.usage(prefix=ctx.prefix),
                    inline=False)

        if isinstance(cmd, car.TextCommand) and len(cmd.aliases) > 0:
            e.add_field(name="Aliases",
                        value=' '.join(f"`{a}`" for a in cmd.aliases),
                        inline=False)

        if len(cmd.checks) > 0:
            descs = []
            for c in cmd.checks:
                descs.append(await c.desc(ctx))
            e.add_field(name="Checks",
                        value="This command:\n"+ '\n'.join(descs),
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
        ] = None
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
            await ctx.respond(embed=await self.cmdlist_embed(
                ctx, self.bot.cog_handler.text_commands,
                title=title, description=desc
            ))
            return

        cmd = self.bot.cog_handler.text_commands.get(command)
        if cmd is None:
            raise car.ArgumentError(f"Invalid command! Use `{ctx.prefix}help` "
                                "to view the list of commands.", 'command')

        await ctx.respond(embed=await self.cmdhelp_embed(
                ctx, cmd, f"Text command: {cmd.name}"))

    @car.mixed_command(text_name="help_slash", slash_name="help")
    async def slash_help(
        self,
        ctx: car.SlashContext,
        command: A[
            Optional[str],
            ("the name of a slash command; if unspecified, returns the slash "
             "command list")
        ] = None
    ):
        """Views slash command help / displays the usage of a slash command"""
        if command is None:
            title = "Slash Command List"
            desc = (
                "Use `/help [command]` to view command usage\n"
                f"Use `/help_text` or `(insert alt help here)` to view "
                "the list of text commands"
            )
            await ctx.respond(embed=await self.cmdlist_embed(
                ctx, self.bot.cog_handler.slash_commands,
                sep=True, title=title, description=desc
            ))
            return

        cmd = self.bot.cog_handler.slash_commands.get(command)
        if cmd is None:
            raise car.ArgumentError(f"Invalid command! Use `/help` to view the "
                                "list of commands.", 'command')

        await ctx.respond(embed=await self.cmdhelp_embed(
                ctx, cmd, f"Slash command: {cmd.name}"))

