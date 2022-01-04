from abc import ABCMeta, abstractmethod
from typing import Any, Optional, Union, TYPE_CHECKING
import discord
from loguru import logger
from discord import (
    AllowedMentions, Message, TextChannel, Guild, PartialMessageable, Thread,
    Member, User, Embed, Interaction, WebhookMessage
)

from .exception import ContextError
from .util import generate_repr
if TYPE_CHECKING:
    from .bot import Bot


__all__ = [
    'Context',
    'SlashContext',
    'TextContext'
]

class Context(metaclass=ABCMeta):
    def __init__(
        self,
        *,
        channel: Union[TextChannel, PartialMessageable, Thread],
        guild: Optional[Guild],
        author_user: Union[Member, User],
        bot: 'Bot',
        prefix: str
    ):
        self.channel = channel
        self._guild = guild
        self.author_user = author_user
        self.bot = bot
        self.prefix = prefix

        self.args: dict[str, Any] = {} # filled by cog_handler

    def __repr__(self) -> str:
        return generate_repr("Context", (
            ('channel', self.channel),
            ('guild', self._guild),
            ('author', self.author),
            ('prefix', self.prefix)
        ))

    def is_dm(self) -> bool:
        return self._guild is None

    @property
    def author(self) -> Member:
        if isinstance(self.author_user, User):
            raise ContextError("This command should be set to guild-only!")
        return self.author_user

    @property
    def guild(self) -> Guild:
        if self._guild is None:
            raise ContextError("This command should be set to guild-only!")
        return self._guild

    async def send(self, content: Optional[str] = None, **kwargs) -> Message:
        kwargs['allowed_mentions'] = kwargs.get('allowed_mentions',
                                                AllowedMentions.none())
        return await self.channel.send(content, **kwargs)

    @abstractmethod
    async def defer(self) -> None:
        pass

    @abstractmethod
    async def respond(self, content: Optional[str] = None, **kwargs) -> None:
        pass

    @abstractmethod
    async def edit_response(self, **kwargs) -> None:
        pass

    @abstractmethod
    async def delete_response(self) -> None:
        pass

    # @abstractmethod
    # async def followup(self, *args, **kwargs) -> None:
        # pass


class SlashContext(Context):
    def __init__(
        self,
        *,
        channel: Union[TextChannel, PartialMessageable, Thread],
        guild: Optional[Guild],
        author_user: Union[Member, User],
        bot: 'Bot',
        prefix: str,
        interaction: Interaction
    ):
        super().__init__(channel=channel, guild=guild,
                         author_user=author_user, bot=bot, prefix=prefix)
        self.interaction = interaction

    def __repr__(self) -> str:
        return generate_repr("Context", (
            ('channel', self.channel),
            ('guild', self._guild),
            ('author', self.author),
            ('prefix', self.prefix),
            ('interaction', self.interaction)
        ))

    @classmethod
    def from_interaction(cls, bot: 'Bot', interaction: Interaction):
        if not isinstance(interaction.channel, (TextChannel,
                                                PartialMessageable,
                                                Thread)) \
                or interaction.user is None:
            raise ContextError("Invalid interaction")
        return cls(channel=interaction.channel, guild=interaction.guild,
                   author_user=interaction.user, bot=bot, prefix="/",
                   interaction=interaction)

    async def defer(self) -> None:
        await self.interaction.response.defer()

    async def respond(self, content: Optional[str] = None, **kwargs) -> None:
        await self.interaction.response.send_message(content, **kwargs)

    async def edit_response(self, **kwargs) -> None:
        await self.interaction.edit_original_message(**kwargs)

    async def delete_response(self) -> None:
        await self.interaction.delete_original_message()


class TextContext(Context):
    def __init__(
        self,
        *,
        channel: Union[TextChannel, PartialMessageable, Thread],
        guild: Optional[Guild],
        author_user: Union[Member, User],
        bot: 'Bot',
        prefix: str,
        message: Message
    ):
        super().__init__(channel=channel, guild=guild, author_user=author_user,
                         bot=bot, prefix=prefix)
        self.message = message
        self._response: Optional[Message] = None

    def __repr__(self) -> str:
        return generate_repr("Context", (
            ('message', self.message),
            ('channel', self.channel),
            ('guild', self._guild),
            ('author', self.author),
            ('prefix', self.prefix),
        ))

    @classmethod
    def from_message(cls, bot: 'Bot', message: Message, prefix: str):
        if not isinstance(message.channel, (TextChannel, PartialMessageable,
                                            Thread)):
            raise ContextError("Invalid message")

        return cls(message=message, channel=message.channel,
                   author_user=message.author, guild=message.guild,
                   bot=bot, prefix=prefix)

    async def defer(self) -> None:
        # TODO: make this last longer than 10 seconds if needed
        await self.channel.trigger_typing()

    async def respond(self, content: Optional[str] = None, **kwargs) -> None:
        self._response = await self.send(
            content, **kwargs, reference=self.message.to_reference()
        )

    async def edit_response(self, **kwargs) -> None:
        await self._response.edit(**kwargs)

    async def delete_response(self) -> None:
        await self._response.delete()

