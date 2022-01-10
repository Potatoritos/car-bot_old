from typing import Any


__all__ = [
    'join_last',
    'generate_repr',
    'zwsp'
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

