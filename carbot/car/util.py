from typing import Any


__all__ = [
    'join_last',
    'generate_repr'
]


def join_last(lst: list[str], last_sep: str) -> str:
    if len(lst) == 1:
        return lst[0]
    return f", {last_sep} ".join([", ".join(lst[:-1])] + lst[-1:])

def generate_repr(name: str, attrs: tuple[tuple[str, Any], ...]) -> str:
    inner = ' '.join(f"{k}={repr(v)}" for k, v in attrs)
    return f"<{name} {inner}>"

