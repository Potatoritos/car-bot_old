from typing import Callable, Optional, Type, TYPE_CHECKING
from .command import Command, TextCommand, SlashCommand, MixedCommandContainer
import inspect
if TYPE_CHECKING:
    from .bot import Bot


__all__ = [
    'Cog'
]

class Cog:
    checks: tuple[Callable, ...] = ()
    category: str = "Uncategorized"

    def __init__(self, bot: 'Bot'):
        self.text_commands: list[TextCommand] = []
        self.slash_commands: list[SlashCommand] = []
        self.bot = bot

        for _, obj in inspect.getmembers(self):
            if isinstance(obj, Command):
                self._add_command(obj)
            elif isinstance(obj, MixedCommandContainer):
                self._add_command(obj.text_command)
                self._add_command(obj.slash_command)

    def _add_command(self, cmd: Command):
        if cmd.category == "Uncategorized":
            cmd.category = self.category

        cmd.parent_cog = self

        for check_deco in self.checks:
            check = check_deco()
            cmd.add_check(check)

        if isinstance(cmd, TextCommand):
            self.text_commands.append(cmd)
        elif isinstance(cmd, SlashCommand):
            self.slash_commands.append(cmd)

