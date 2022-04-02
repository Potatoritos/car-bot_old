from typing import Generator, Optional
from .exception import CheckError


__all__ = [
    'Tokenizer',
    'filter_kwargs'
]

class Tokenizer:
    def __init__(self, text: str):
        self.text = text
        self.index: int = 0
        self.word: list[str] = []

    def _add_char(self) -> None:
        if self.text[self.index] == '\\' and self.index < len(self.text)-1:
            # for python 3.10
            # match self.text[self.index + 1]:
                # case '\\' | '"' as escaped:
                    # self.word.append(escaped)
                # case 'n':
                    # self.word.append('\n')
                # case _ as escaped:
                    # self.word.append('\\' + escaped)

            c = self.text[self.index+1]
            if c == '\\' or c == '"':
                self.word.append(c)
            elif c == 'n':
                self.word.append('\n')
            else:
                self.word.append('\\' + c)

            self.index += 1

        else:
            self.word.append(self.text[self.index])

    def _skip_spaces(self) -> None:
        while self.index < len(self.text) and self.text[self.index] == ' ':
            self.index += 1

    def next_token(self, index: Optional[int] = None) -> str:
        if index is not None:
            self.index = index
        quoted: bool = False

        self._skip_spaces()

        while self.index < len(self.text) and \
                (quoted or self.text[self.index] != ' '):

            if self.text[self.index] == '"':
                quoted = not quoted
            else:
                self._add_char()

            self.index += 1

        res = ''.join(self.word)
        self.word = []

        return res

    def is_eof(self) -> bool:
        self._skip_spaces()
        return self.index >= len(self.text)

    def get_remaining(self) -> str:
        return self.text[self.index:].strip()

    def reset(self) -> None:
        self.index = 0

    def tokens(self) -> Generator[str, None, None]:
        while not self.is_eof():
            yield self.next_token()
        self.reset()

def filter_kwargs(content: str) -> tuple[str, dict[str, str]]:
    spl = []
    kwargs: dict[str, str] = {}
    quoted = False
    content = " " + content
    tok = Tokenizer(content)

    i = 0
    while i < len(content):
        if content[i] == '"':
            quoted = not quoted

        if (not quoted) and i < len(content)-3 and content[i:i+2] == ' -':
            name = tok.next_token(i+2)
            if tok.is_eof():
                raise CheckError(f"You didn't give kwarg `-{name}` a value!")
            kwargs[name] = tok.next_token()
            i = tok.index
        else:
            spl.append(content[i])
            i += 1

    return (''.join(spl).strip(), kwargs)

