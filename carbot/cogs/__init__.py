# from .test_cog import TestCog
from .admin import Admin
from .guild import Guild
from .image import Image
from .meta import Meta
from .moderation import Moderation
from .pinboard import Pinboard
from .simulation import Simulation
from .sound import Sound
from .text import Text
from .typing import Typing
from .utility import Utility
from .wab import Wab


to_load = (
    Admin,
    Guild,
    Image,
    Meta,
    Moderation,
    Pinboard,
    Simulation,
    Sound,
    Text,
    Typing,
    Utility,
    Wab,
)

