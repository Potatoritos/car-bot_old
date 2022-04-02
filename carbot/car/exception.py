from typing import Optional


__all__ = [
    'CarException',
    'CogError',
    'ContextError',
    'UserError',
    'CheckError',
    'CommandError',
    'ArgumentError'
]

class CarException(Exception):
    pass

class CogError(CarException):
    pass

class ContextError(CarException):
    pass

class UserError(CarException):
    def __init__(self, error_msg: str):
        super().__init__()
        self.error_msg = error_msg

class CheckError(UserError):
    pass

class CommandError(UserError):
    pass

class ArgumentError(UserError):
    def __init__(self, error_msg: str, highlight: Optional[str] = None):
        super().__init__(error_msg)
        self.highlight = highlight

