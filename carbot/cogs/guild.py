from typing import Annotated as A, Optional
import discord
import car


class Guild(car.Cog):
    category = "Server"

    @car.mixed_command(aliases=("set", "config", "conf"))
    @car.guild_only()
    @car.requires_permissions(manage_guild=True)
    async def settings(
        self,
        ctx: car.Context,
        prefix: Optional[str] = None,
        join_message_enabled: Optional[bool] = None,
        join_message: A[
            Optional[str],
            ("{name}, {discrim}, {id}, and {mention} are replaced with their "
             "respective values")
        ] = None,
        leave_message_enabled: Optional[bool] = None,
        leave_message: A[
            Optional[str],
            ("{name}, {discrim}, {id}, and {mention} are replaced with their "
             "respective values")
        ] = None,
        joinleave_channel: Optional[discord.TextChannel] = None,
        pinboard_enabled: Optional[bool] = None,
        pinboard_channel: Optional[discord.TextChannel] = None
    ):
        """Views server settings. Specify arguments to change values"""
        for name, new_val in ctx.args.items():
            if new_val is None:
                continue
            if isinstance(new_val, discord.TextChannel):
                new_val = new_val.id
            self.bot.guild_settings.update(ctx.guild.id, name, new_val)

        e = discord.Embed(title="Settings")
        r = self.bot.guild_settings.row(ctx.guild.id)
        print(r)
        e.add_field(name="prefix", value=r['prefix'], inline=False)
        e.add_field(name="join_message_enabled",
                    value="Yes" if r['join_message_enabled'] else "No",
                    inline=False)
        e.add_field(name="join_message",
                    value="*(None)*" if r['join_message'] == ""
                          else r['join_message'],
                    inline=False)
        e.add_field(name="leave_message_enabled",
                    value="Yes" if r['leave_message_enabled'] else "No",
                    inline=False)
        e.add_field(name="leave_message",
                    value="*(None)*" if r['leave_message'] == ""
                          else r['leave_message'],
                    inline=False)
        c = discord.utils.get(ctx.guild.channels, id=r['joinleave_channel'])
        e.add_field(name="joinleave_channel",
                    value="*(None)*" if c is None else c.mention,
                    inline=False)
        e.add_field(name="pinboard_enabled",
                    value="Yes" if r['pinboard_enabled'] else "No",
                    inline=False)
        c = discord.utils.get(ctx.guild.channels, id=r['pinboard_channel'])
        e.add_field(name="pinboard_channel",
                    value="*(None)*" if c is None else c.mention,
                    inline=False)
        await ctx.respond(embed=e)

    @car.listener
    async def on_message(self, msg: discord.Message):
        print(msg.content)

