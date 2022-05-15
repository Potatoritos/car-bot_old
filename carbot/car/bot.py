import discord
import asyncio
import json
import sqlite3
from loguru import logger

from .cog_handler import CogHandler
from .context import TextContext, SlashContext
from .db import DBTable, DBColumn
from .enums import CommandType, ClearanceLevel


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
        self.guild_settings = DBTable(self.con, 'guild_settings', (
            DBColumn('guild_id', 0, is_primary=True),
            DBColumn('prefix', "]"),
            DBColumn('join_message_enabled', False),
            DBColumn('join_message', ""),
            DBColumn('leave_message_enabled', False),
            DBColumn('leave_message', ""),
            DBColumn('joinleave_channel', 0),
            DBColumn('pinboard_enabled', False),
            DBColumn('pinboard_channel', 0),
            DBColumn('modlog_enabled', False),
            DBColumn('modlog_channel', 0),
            DBColumn('vclog_enabled', False),
            DBColumn('vclog_channel', 0)
        ))

        self.user_admin = DBTable(self.con, 'user_admin', (
            DBColumn('user_id', 0, is_primary=True),
            DBColumn('clearance', 0)
        ))

    async def process_message(self, msg: discord.Message) -> None:
        if not isinstance(msg.channel, (discord.TextChannel,
                                        discord.DMChannel)):
            return

        if msg.author.bot:
            return

        # if msg.author.id not in self.user_admin:
            # self.user_admin.insert(msg.author.id)

        # if self.user_admin.select('clearance', 'where user_id=?',
                                  # (msg.author.id,)) <= ClearanceLevel.BANNED:
            # return

        if msg.guild is None:
            prefix = "]"
        else:
            if msg.guild.id not in self.guild_settings:
                self.guild_settings.insert(guild_id=msg.guild.id)

            prefix = self.guild_settings.select('prefix', 'where guild_id=?',
                                                (msg.guild.id,))

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
        if old.content == new.content:
            return

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

