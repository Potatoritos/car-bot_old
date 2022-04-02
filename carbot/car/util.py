from typing import Any
from os.path import exists


__all__ = [
    'join_last',
    'generate_repr',
    'zwsp',
    'temp_file'
]


def join_last(lst: list[str], last_sep: str) -> str:
    if len(lst) == 1:
        return lst[0]
    return f", {last_sep} ".join([", ".join(lst[:-1])] + lst[-1:])

def generate_repr(name: str, attrs: tuple[tuple[str, Any], ...]) -> str:
    inner = ' '.join(f"{k}={repr(v)}" for k, v in attrs)
    return f"<{name} {inner}>"

def zwsp(s: str, chars: str) -> str:
    ZWSP = '​'
    for c in chars:
        s = s.replace(c, ZWSP + c)
    return s

def temp_file() -> str:
    i = 0
    while i := i+1:
        name = f"dl/temp_file_{i}"
        if not exists(f"dl/temp_file_{i}"):
            return name

