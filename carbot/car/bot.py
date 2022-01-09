import discord
import asyncio
import json
import sqlite3
from loguru import logger

from .cog_handler import CogHandler
from .context import TextContext, SlashContext
from .db import PersistentStorage, Table, Column
from .enums import CommandType


__all__ = [
    'Bot'
]

class Bot(discord.Client):
    def __init__(self, *args, **kwargs):
        intents = discord.Intents().default()
        intents.members = True
        super().__init__(intents=intents, *args, **kwargs)

        self.cog_handler = CogHandler(self)

        self.con = sqlite3.connect('car.db')
        self.guild_settings = PersistentStorage(Table(
            self.con, 'guild_settings', (
                Column('guild_id', 0, primary_key=True),
                Column('prefix', "]"),
                Column('join_message_enabled', False),
                Column('join_message', ""),
                Column('leave_message_enabled', False),
                Column('leave_message', ""),
                Column('joinleave_channel', 0),
                Column('pinboard_enabled', False),
                Column('pinboard_channel', 0)
            )        
        ))

    async def process_message(self, msg: discord.Message) -> None:
        if not isinstance(msg.channel, (discord.TextChannel,
                                        discord.DMChannel)):
            return

        if msg.author.bot:
            return

        if msg.guild is None:
            prefix = "]"
        else:
            prefix = self.guild_settings.cell(msg.guild.id, 'prefix')
        if not msg.content.startswith(prefix) \
                or len(msg.content) <= len(prefix):
            return

        idx = msg.content.find(' ', len(prefix))
        if idx == -1:
            idx = len(msg.content)
        name = msg.content[len(prefix) : idx]

        cmd = self.cog_handler.text_commands.get(
            name, self.cog_handler.text_aliases.get(name)
        )
        if cmd is None:
            return

        content = msg.content[idx:]
        ctx = TextContext.from_message(self, msg, prefix)

        # await self.cog_handler.run_command_text(ctx, cmd, content)
        asyncio.create_task(self.cog_handler.run_command_text(ctx, cmd,
                                                              content))

    async def on_message(self, msg: discord.Message) -> None:
        await self.process_message(msg)

    async def on_message_edit(self, old: discord.Message,
                              new: discord.Message) -> None:
        await self.process_message(new)

    async def process_interaction(self, interaction: discord.Interaction
                                  ) -> None:
        data = interaction.data
        if data['type'] == CommandType.CHAT_INPUT: # type: ignore[index,typeddict-item]
            ctx = SlashContext.from_interaction(self, interaction)
            # await self.cog_handler.run_command_slash(ctx, data) # type: ignore[arg-type]
            asyncio.create_task(self.cog_handler.run_command_slash(ctx, data)) # type: ignore[arg-type]

    async def on_interaction(self, interaction: discord.Interaction) -> None:
        await self.process_interaction(interaction)

    async def on_ready(self) -> None:
        if self.user is None:
            return
        logger.success(f"Logged in as {self.user.name}#"
                       f"{self.user.discriminator} (id: {self.user.id})")

    # called by discord.Client whenever an event occurs
    def dispatch(self, event, *args, **kwargs):
        super().dispatch(event, *args, **kwargs)
        self.cog_handler.run_listeners('on_' + event, args, kwargs)

    def run(self, *args, **kwargs) -> None:
        logger.info("Logging in...")
        super().run(*args, **kwargs)

