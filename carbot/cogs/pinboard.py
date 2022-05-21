from typing import Annotated as A, Optional
import discord
from loguru import logger
import car


class Pinboard(car.Cog):
    category = "Pinboard"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reacted_msgs = {}

        # self.pinned = car.DBTable(self.bot.con, 'pinboard_pinned', (
            # car.DBColumn('id', 0, is_primary=True),
            # car.DBColumn('user_id', 0),
            # car.DBColumn('stars', 0),
            # car.DBColumn('msg_link', "")
        # ))

        # self.lb = car.DBTable(self.con, 'pinboard_lb', (
            # DBColumn('user_id', 0, is_primary=True),
            # DBColumn('total_stars', 0),
            # DBColumn('total_pinned', 0)
        # ))

    # @car.slash_command_group(name="pinboard")
    # async def _(self, ctx): pass

    # @car.mixed_command(slash_name="pinboard lb")
    # async def pinboardlb(self, ctx, page: Optional[int]):
        # """Views pins with the highest number of stars"""

    # @car.text_command()
    # @car.requires_clearance(car.ClearanceLevel.TRUSTED)
    # async def pbmanuadd(self, ctx, msg_id: int):
        # """Manually adds a message to pinboard"""
        # msg = await channel.fetch_message(msg_id)
        # await self.pin_message(msg, check=False)

    # @car.text_command(hidden=True)
    # @car.requires_clearance(car.ClearanceLevel.ADMIN)
    # async def pinboardlb_initchannel(self, ctx):
        # """Initializes pinboard leaderboard with messages from ctx.channel"""

        # await ctx.respond("scanning...")
        # logger.info("Starting pinboard leaderboard initialization")

        # bot_ids = (
            # 745018778579894285,
            # 807311113045409823,
            # 975247820959412284
        # )

        # cur = self.bot.con.cursor()

        # async for msg in ctx.channel.history(limit=None, oldest_first=True):
            # if msg.author.id not in bot_ids:
                # continue

            # if not msg.content.startswith(":star:"):
                # continue

            # try:
                # stars = int(msg.content.split('x')[-1])
            # except ValueError:
                # continue

            # user_id = int(s[s.find('<@')+2:].split('>')[0])
            # # msg_link = s[s.find('(https://dis')+1:].split(')')[0]
            # msg_link = msg.jump_url

            # cur.execute(
                # "INSERT INTO pinboard_pinned VALUES(NULL, ?, ?, ?)",
                # (user_id, stars, msg_link)
            # )
            # # if user_id not in self.lb:
                # # self.lb.insert(user_id=user_id, total_stars=stars,
                               # # total_pinned=1)
            # # else:
                # # cur.execute((
                    # # "UPDATE pinboard_lb SET total_stars = total_stars + ?"
                    # # ", total_pinned = total_pinned + 1"
                # # ), (stars,))


        # self.bot.con.commit()

        # await ctx.send("scanning done")

    async def pin_message(self, cfg, reaction, msg):
        if msg.id in self.reacted_msgs \
                and not isinstance(self.reacted_msgs, bool):
            m = self.reacted_msgs[msg.id]
            if not m.content.split(' ')[-1] == f"**x{reaction.count}**":
                await m.edit(
                    content=f"{m.content.split(' ')[0]} **x{reaction.count}**"
                )
            return

        self.reacted_msgs[msg.id] = True # placeholder

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
                or reaction.count < cfg['pinboard_stars']:
                # or msg.id in self.reacted_msgs:
            return

        await self.pin_message(cfg, reaction, msg)

