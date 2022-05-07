from typing import Any
from os.path import exists


__all__ = [
    'join_last',
    'generate_repr',
    'zwsp',
    'zwsp_md',
    'without_md_formatting',
    'temp_file'
]


def join_last(lst: list[str], last_sep: str) -> str:
    if len(lst) == 1:
        return lst[0]
    comma = ', '[len(lst) == 2]
    return f"{comma} {last_sep} ".join([", ".join(lst[:-1])] + lst[-1:])

def generate_repr(name: str, attrs: tuple[tuple[str, Any], ...]) -> str:
    inner = ' '.join(f"{k}={repr(v)}" for k, v in attrs)
    return f"<{name} {inner}>"

def zwsp(s: str, chars: str) -> str:
    ZWSP = '​'
    for c in chars:
        s = s.replace(c, ZWSP + c)
    return s

def zwsp_md(s: str) -> str:
    return zwsp(s, '`*_')

def without_md_formatting(s: str) -> str:
    return s.replace('*', '').replace('`', '')

def temp_file() -> str:
    i = 0
    while i := i+1:
        name = f"dl/temp_file_{i}"
        if not exists(f"dl/temp_file_{i}"):
            return name

    return ""

