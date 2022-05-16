from typing import Annotated as A, Optional
import discord
from loguru import logger
import car


class Pinboard(car.Cog):
    category = "Pinboard"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @car.text_command(hidden=True)
    @car.requires_clearance(car.ClearanceLevel.ADMIN)
    async def pinboardlb_initchannel(self, ctx):
        """Adds all pinboarded messages in channel to pinboard leaderboard"""
        pass

    @car.text_command()
    async def pbtest(self, ctx):
        pass

    @car.listener
    async def on_reaction_add(self, reaction, user):
        msg = reaction.message

        if msg.guild.id not in self.bot.guild_settings:
            self.bot.guild_settings.insert(guild_id=member.guild.id)

        cfg = self.bot.guild_settings.select(
            'pinboard_enabled, pinboard_channel, pinboard_stars',
            'WHERE guild_id=?', (msg.author.guild.id,)
        )

        if not cfg['pinboard_enabled'] \
                or reaction.count < cfg['pinboard_stars'] \
                or msg.id in self.reacted_msgs:
            return

        if msg.id in self.reacted_msgs:
            m = self.reacted_msgs[msg.id]
            if not m.content.split(' ')[-1] == f"**x{reaction.count}**":
                await m.edit(
                    content=f"{m.content.split(' ')[0]} **x{reaction.count}**"
                )
            return

        self.reacted_msgs[msg.id] = True # until the pinboard msg is sent

        channel = discord.utils.get(msg.guild.channels,
                                    id=cfg['pinboard_channel'])

        if channel is None:
            return

        desc = (f"[[Jump]]({msg.jump_url}) {msg.author.mention} in"
                f"{msg.channel.mention}\n\n{msg.content}")

        e = discord.Embed(description=desc)
        if len(msg.attachments) > 0:
            e.set_image(url=msg.attachments[0].url)
            e.add_field(
                name="Attachments",
                value='\n'.join(f"[{a.filename}]({a.url})"
                                for a in msg.attachments)
            )

        e.set_author(
            name=f"{msg.author.name}#{msg.author.discriminator}",
            icon_url=msg.author.avatar.url
        )

        m = await channel.send(f"{reaction.emoji} **x{reaction.count}**",
                               embed=e)
        self.reacted_msgs[msg.id] = m

