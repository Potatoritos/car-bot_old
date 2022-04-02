from enum import Enum


__all__ = [
    'CommandType'
    'OptionType'
]

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

