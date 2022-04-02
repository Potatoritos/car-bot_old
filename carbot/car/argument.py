from typing import Optional, Union, Any, Type, overload, get_args, get_origin
import inspect
import discord
from loguru import logger

from .enums import OptionType
from .util import join_last


__all__ = [
    'Argument',
    'FromChoices',
    'InRange'
]

option_types = {
    str: OptionType.STRING,
    int: OptionType.INTEGER,
    bool: OptionType.BOOLEAN,
    float: OptionType.NUMBER,
    discord.Member: OptionType.USER,
    discord.Role: OptionType.ROLE,
    discord.TextChannel: OptionType.CHANNEL
}

class Argument:
    def __init__(
        self,
        *,
        name: str,
        arg_type: Type,
        desc: Optional[str] = None,
        required: bool = True,
        choices: Optional[Union[list[dict[str, str]], list[dict[str, int]],
                                list[dict[str, float]]]] = None,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        default: Optional[Any] = None
    ):
        self.name = name
        self.arg_type = arg_type
        self.desc = desc
        self.required = required
        self.choices = choices
        self.min_value = min_value
        self.max_value = max_value
        self.default = default

    @classmethod
    def from_hint(cls, hint, **kwargs):
        if isinstance(hint, type):
            return cls(arg_type=hint, **kwargs)

        if get_origin(hint) is Union:
            assert type(None) in get_args(hint) and len(get_args(hint)) == 2
            assert kwargs['default'] is not inspect.Parameter.empty
            if not isinstance(get_args(hint)[0], type):
                return cls.from_hint(get_args(hint)[0], **kwargs)

            return cls(arg_type=get_args(hint)[0], required=False, **kwargs)
        else: # if hint is a typing.Annotated[...]
            hint_args = get_args(hint)
            for a in hint_args[1:]:
                if isinstance(a, str):
                    kwargs['desc'] = a
                elif isinstance(a, FromChoices):
                    kwargs['choices'] = a.json()
                elif isinstance(a, InRange):
                    kwargs['min_value'] = a.lower
                    kwargs['max_value'] = a.upper

            return cls.from_hint(hint_args[0], **kwargs)

    @property
    def label(self) -> str:
        return f"[{self.name}]" if self.required else f"({self.name})"
    
    def usage_label(self, slash: bool = True) -> str:
        if slash:
            code, bold, italics, delim, sp = '', '', '', '', ' '
        else:
            code, bold, italics, delim, sp = '`', '**', '*', ': ', ''

        lb: list[str] = [] if slash else [f"{code}{self.label}{code}"]

        if not self.required:
            if self.default is not None:
                default = self.default
                if default is True:
                    default = "yes"
                elif default is False:
                    default = "no"
                lb.append(f"{italics}(default: {default}){italics}{sp}")
            else:
                lb.append(f"{italics}(optional){italics}{sp}")

        if self.choices is None:
            type_descs = {
                int: "an integer",
                float: "a number",
                str: "a string",
                bool: f"{code}yes{code} or {code}no{code}",
                discord.Member: "a member",
                discord.TextChannel: "a text channel",
                discord.VoiceChannel: "a voice channel",
                discord.Role: "a role"
            }
            lb.append(f"{delim}{bold}{type_descs[self.arg_type]}")
        elif slash:
            lb.append(f"one of the above options")
        else:
            lb.append(f"{delim}{bold}" + join_last([f"{code}{c['name']}{code}"
                                                 for c in self.choices], "or"))


        if self.min_value is not None and self.max_value is not None:
            lb.append(f" between {self.min_value} and {self.max_value}, "
                      "inclusive")
        elif self.min_value is not None:
            lb.append(f" at least {self.min_value}")
        elif self.max_value is not None:
            lb.append(f" at most {self.max_value}")

        lb.append(bold)

        if self.desc is not None:
            lb.append(f"—{self.desc}")

        return ''.join(lb)

    def json(self) -> dict[str, Any]:
        data = {
            'type': option_types[self.arg_type],
            'name': self.name,
            'description': self.usage_label(slash=True),
            'required': self.required,
            'choices': self.choices,
            'min_value': self.min_value,
            'max_value': self.max_value
        }
        if self.arg_type is discord.TextChannel:
            data['channel_types'] = [0]
        # elif self.arg_type is discord.VoiceChannel:
            # data['channel_types'] = 2
        elif self.arg_type is bool:
            data['type'] = option_types[str]
            data['choices'] = [
                {'name': "Yes", 'value': "1"},
                {'name': "No", 'value': "0"}
            ]

        return data


class FromChoices:
    def __init__(self, choices: Union[dict[str, int],
                                      dict[str, float],
                                      dict[str, str]]):
        self.choices = choices

    def json(self):
        return [{'name': name, 'value': val}
                for name, val in self.choices.items()]

class InRange:
    def __init__(
        self,
        lower: Optional[int] = None,
        upper: Optional[int] = None
    ):
        self.lower = lower
        self.upper = upper

