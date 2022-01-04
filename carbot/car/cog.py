from typing import Callable, Optional, Type
from .command import Command, TextCommand, SlashCommand, MixedCommandContainer
import inspect


__all__ = [
    'Cog'
]

class Cog:
    global_checks: tuple[Callable, ...] = ()
    global_category: Optional[str] = None

    def __init__(self):
        self.text_commands: list[TextCommand] = []
        self.slash_commands: list[SlashCommand] = []

        for _, obj in inspect.getmembers(self):
            if isinstance(obj, Command):
                self._add_command(obj)
            elif isinstance(obj, MixedCommandContainer):
                self._add_command(obj.text_command)
                self._add_command(obj.slash_command)

    def _add_command(self, cmd: Command):
        if cmd.category is None:
            cmd.category = self.global_category

        cmd.parent_cog = self

        for check_deco in self.global_checks:
            check = check_deco()
            cmd.add_check(check)

        if isinstance(cmd, TextCommand):
            self.text_commands.append(cmd)
        elif isinstance(cmd, SlashCommand):
            self.slash_commands.append(cmd)

