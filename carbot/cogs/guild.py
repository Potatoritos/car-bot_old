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
        pinboard_channel: Optional[discord.TextChannel] = None,
        modlog_enabled: Optional[bool] = None,
        modlog_channel: Optional[discord.TextChannel] = None,
        vclog_enabled: Optional[bool] = None,
        vclog_channel: Optional[discord.TextChannel] = None
    ):
        """Views server settings. Specify arguments to change values"""
        vals = {name: new_val if not isinstance(new_val, discord.TextChannel)
                else new_val.id
                for name, new_val in ctx.args.items()}

        if vals:
            self.bot.guild_settings.update(ctx.guild.id, **vals)

        # for name, new_val in ctx.args.items():
            # if new_val is None:
                # continue
            # if isinstance(new_val, discord.TextChannel):
                # new_val = new_val.id
            # self.bot.guild_settings.update(ctx.guild.id, **{name: new_val})

        e = discord.Embed(title="Settings")
        r = self.bot.guild_settings.select('*', 'where guild_id=?',
                                           (ctx.guild.id,))

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
        c = discord.utils.get(ctx.guild.text_channels,
                              id=r['joinleave_channel'])
        e.add_field(name="joinleave_channel",
                    value="*(None)*" if c is None else c.mention,
                    inline=False)

        e.add_field(name="pinboard_enabled",
                    value="Yes" if r['pinboard_enabled'] else "No",
                    inline=False)
        c = discord.utils.get(ctx.guild.text_channels,
                              id=r['pinboard_channel'])
        e.add_field(name="pinboard_channel",
                    value="*(None)*" if c is None else c.mention,
                    inline=False)

        e.add_field(name="modlog_enabled",
                    value="Yes" if r['modlog_enabled'] else "No",
                    inline=False)
        c = discord.utils.get(ctx.guild.text_channels,
                              id=r['modlog_channel'])
        e.add_field(name="modlog_channel",
                    value="*(None)*" if c is None else c.mention,
                    inline=False)

        e.add_field(name="vclog_enabled",
                    value="Yes" if r['vclog_enabled'] else "No",
                    inline=False)
        c = discord.utils.get(ctx.guild.text_channels,
                              id=r['vclog_channel'])
        e.add_field(name="vclog_channel",
                    value="*(None)*" if c is None else c.mention,
                    inline=False)

        await ctx.respond(embed=e)

    @car.listener
    async def on_member_join(self, member: discord.Member):
        if member.guild.id not in self.bot.guild_settings:
            self.bot.guild_settings.insert(guild_id=member.guild.id)
            
        r = self.bot.guild_settings.select(
            'join_message_enabled, joinleave_channel, join_message',
            'where guild_id=?', (member.guild.id,))

        if not r['join_message_enabled']:
            return

        c = discord.utils.get(member.guild.text_channels,
                              id=r['joinleave_channel'])
        if c is None:
            return

        greeting = car.zwsp(
            r['join_message'].format(
                username=member.name, name=member.name,
                discrim=member.discriminator,
                discriminator=member.discriminator,
                mention=member.mention, ping=member.mention,
                id=member.id
            ),
            '/'
        )
        allowed = discord.AllowedMentions(everyone=False, roles=False)
        await c.send(greeting, allowed_mentions=allowed)


    @car.listener
    async def on_member_remove(self, member: discord.Member):
        if member.guild.id not in self.bot.guild_settings:
            self.bot.guild_settings.insert(guild_id=member.guild.id)
            
        r = self.bot.guild_settings.select(
            'leave_message_enabled, joinleave_channel, leave_message',
            'where guild_id=?', (member.guild.id,))

        if not r['leave_message_enabled']:
            return

        c = discord.utils.get(member.guild.text_channels,
                              id=r['joinleave_channel'])
        if c is None:
            return

        farewell = car.zwsp(
            r['leave_message'].format(
                username=member.name, name=member.name,
                discrim=member.discriminator,
                discriminator=member.discriminator,
                mention=member.mention, ping=member.mention,
                id=member.id
            ),
            '/'
        )

        allowed = discord.AllowedMentions(everyone=False, roles=False)
        await c.send(farewell, allowed_mentions=allowed)

