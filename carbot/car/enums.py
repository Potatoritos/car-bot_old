from enum import Enum


__all__ = [
    'ChannelType',
    'CommandType',
    'OptionType',
    'ClearanceLevel'
]

class ChannelType(int, Enum):
    GUILD_TEXT = 0
    DM = 1
    GUILD_VOICE = 2
    GROUP_DM = 3
    GUILD_CATEGORY = 4
    GUILD_NEWS = 5
    GUILD_NEWS_THREAD = 10
    GUILD_PUBLIC_TREAD = 11
    GUILD_PRIVATE_THREAD = 12
    GUILD_STAGE_VOICE = 13
    GUILD_DIRECTORY = 14

class CommandType(int, Enum):
    CHAT_INPUT = 1
    USER = 2
    MESSAGE = 3

class OptionType(int, Enum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    NUMBER = 10

class ClearanceLevel(int, Enum):
    BANNED = -1
    DEFAULT = 0
    TRUSTED = 6
    ADMIN = 9

