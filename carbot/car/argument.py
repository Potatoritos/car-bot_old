from typing import Optional, Union, Any, Type, overload, get_args, get_origin
import inspect
import discord
from loguru import logger

from .converter import Converter, default_converters
from .enums import OptionType
from .util import join_last, without_md_formatting


__all__ = [
    'Argument',
]


class Argument:
    def __init__(
        self,
        *,
        name: str,
        arg_type: Type,
        description: Optional[str] = None,
        required: bool = True,
        # choices: Optional[Union[list[dict[str, str]], list[dict[str, int]],
                                # list[dict[str, float]]]] = None,
        # min_value: Optional[Union[int, float]] = None,
        # max_value: Optional[Union[int, float]] = None,
        default: Optional[Any] = None,
        converter: Optional[Converter] = None
    ):
        self.name = name
        self.arg_type = arg_type
        self._description = description
        self.required = required
        # self.choices = choices
        # self.min_value = min_value
        # self.max_value = max_value
        self.default = default
        self.converter = converter or default_converters[arg_type]

    @classmethod
    def from_hint(cls, hint, **kwargs):
        if isinstance(hint, type):
            return cls(arg_type=hint, **kwargs)

        if get_origin(hint) is Union: # if hint is an Optional[T]
            assert type(None) in get_args(hint) and len(get_args(hint)) == 2
            assert kwargs['default'] is not inspect.Parameter.empty

            if not isinstance(get_args(hint)[0], type):
                return cls.from_hint(get_args(hint)[0], **kwargs)

            return cls(arg_type=get_args(hint)[0], required=False, **kwargs)

        else: # if hint is a typing.Annotated[...]
            hint_args = get_args(hint)

            for a in hint_args[1:]:
                if isinstance(a, str):
                    kwargs['description'] = a

                elif isinstance(a, Converter):
                    kwargs['converter'] = a

            return cls.from_hint(hint_args[0], **kwargs)

    @property
    def label(self) -> str:
        return f"[{self.name}]" if self.required else f"({self.name})"
        # return f"[{self.name}]"

    @property
    def slash_description(self) -> str:
        desc = without_md_formatting(self.description)
        if len(desc) <= 100:
            return desc
        elif self._description is None:
            return self.converter.slash_description + self.desc_suffix
        else:
            return f"{self.converter.slash_description}—{self._description}"\
                + self.desc_suffix
    
    @property
    def description(self) -> str:
        if self._description is None:
            desc = f"**{self.converter.description}**"
        else:
            desc = f"**{self.converter.description}**—{self._description}"

        return desc + self.desc_suffix

    @property
    def desc_suffix(self) -> str:
        if self.required:
            return ""
        
        if self.default is not None:
            default = self.default

            if default is True:
                default = "yes"
            elif default is False:
                default = "no"

            return f" *(default: {default})*"
        else:
            return f" *(optional)*"


    def json(self) -> dict[str, Any]:
        data = {
            'name': self.name,
            'description': self.slash_description,
            'required': self.required
        }
        self.converter.modify_slash_data(data)

        return data

