__all__ = [
    'Tokenizer'
]

class Tokenizer:
    def __init__(self, text: str):
        self.text = text
        self.idx: int = 0
        self.word: list[str] = []

    def _add_char(self) -> None:
        if self.text[self.idx] == '\\' and self.idx < len(self.text)-1:
            # for python 3.10
            # match self.text[self.idx + 1]:
                # case '\\' | '"' as escaped:
                    # self.word.append(escaped)
                # case 'n':
                    # self.word.append('\n')
                # case _ as escaped:
                    # self.word.append('\\' + escaped)

            c = self.text[self.idx+1]
            if c == '\\' or c == '"':
                self.word.append(c)
            elif c == 'n':
                self.word.append('\n')
            else:
                self.word.append('\\' + c)

            self.idx += 1

        else:
            self.word.append(self.text[self.idx])

    def _skip_spaces(self) -> None:
        while self.idx < len(self.text) and self.text[self.idx] == ' ':
            self.idx += 1

    def next_token(self) -> str:
        quoted: bool = False

        self._skip_spaces()

        while self.idx < len(self.text) and \
                (quoted or self.text[self.idx] != ' '):

            if self.text[self.idx] == '"':
                quoted = not quoted
            else:
                self._add_char()

            self.idx += 1

        res = ''.join(self.word)
        self.word = []

        return res

    def is_eof(self) -> bool:
        self._skip_spaces()
        return self.idx >= len(self.text)

    def get_remaining(self) -> str:
        return self.text[self.idx:].strip()

    def reset(self) -> None:
        self.idx = 0

