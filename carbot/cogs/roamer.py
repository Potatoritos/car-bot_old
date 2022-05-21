from typing import Annotated as A, Optional
import discord
from loguru import logger
import car


class Roamer(car.Cog):
    category = "R Bongue"

    @car.listener
    async def on_message(self, msg): # called whenever a message is sent
        # return if message was sent by a bot
        if msg.author.bot:
            return

        logger.info(f"{msg.content=}\n{msg.mentions=}\n{msg.author=}\n{msg=}")

        # get member from id
        sparkl = discord.utils.get(msg.guild.members, id=414848078244347904)
        logger.info(f"{sparkl=}")

        logger.info(f"{sparkl.nick=}")
        await sparkl.edit(nick="ballsack")
        logger.info(f"{sparkl.nick=}")

