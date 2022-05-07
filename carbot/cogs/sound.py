import sqlite3
from typing import Annotated as A

import discord
import car


class Sound(car.Cog):
    category = "Sound"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sfx_list = car.DBTable(self.bot.con, 'sfx_list', (
            car.DBColumn('id', 0, is_primary=True),
            car.DBColumn('name', "", is_unique=True),
            car.DBColumn('category', "Uncategorized"),
            car.DBColumn('path', ""),
            car.DBColumn('user_id', 0),
            car.DBColumn('verified', False)
        ))

        self.playlists = car.DBTable(self.bot.con, 'sfx_playlists', (
            car.DBColumn('id', 0, is_primary=True),
            car.DBColumn('name', "", is_unique=True),
            car.DBColumn('sfx', []),
            car.DBColumn('user_id', 0),
            car.DBColumn('verified', False)
        ))

    @car.slash_command_group(name="sfx")
    async def _(self, ctx): pass

    @car.mixed_command(slash_name="sfx add")
    async def sfxadd(
        self,
        ctx: car.Context,
        name: str,
        category: A[str, car.FromChoices({
            'Songs': 'Songs', 'Clips': 'Clips', 'Sounds': 'Sounds',
            'Ambient': 'Ambient', 'None': 'Uncategorized'
        })]
    ):
        """Adds a sound effect (uses the most recently uploaded file)"""

        allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789_"
        if not all(c in allowed_chars for c in name):
            raise car.ArgumentError("Name contains disallowed characters! "
                                    f"Allowed characters: `{allowed_chars}`",
                                    'name')

        attachment = await ctx.last_attachment()

        if '/' in attachment.filename or attachment.filename.count('.') != 1:
            raise car.CommandError(f"``{car.zwsp_md(attachment.filename)}`` - "
                                   "invalid file name!")


        if not attachment.content_type.startswith('audio') and \
                not attachment.content_type.startswith('video'):
            raise car.CommandError(f"``{car.zwsp_md(attachment.filename)}`` "
                                   "does not seem to be an audio file!")

        file_type = attachment.filename.split('.')[-1]
        path = f'./sfx/{name}.{file_type}'

        try:
            self.sfx_list.insert(None, name, category, path, ctx.author.id,
                                 False)
        except sqlite3.IntegrityError:
            raise car.ArgumentError("An sfx with this name already exists!")

        await attachment.save(path)

        await ctx.respond(f"Sound effect `{name}` added!")


    @car.mixed_command(slash_name="sfx list")
    async def sfxlist(self, ctx):
        print(self.sfx_list.select('*'))
        # print(self.sfx_list.all())
        # lst = sorted(self.sfx_list.all(), key=lambda x: x['id'])
        # print(lst)

    # @car.mixed_command(text_name="sfx", slash_name="sfx play",
                       # aliases=["sfxplay"])
    # async def sfxplay(self, ctx):
        # pass

    # @car.mixed_command(slash_name="sfx join")
    # async def sfxjoin(self, ctx):
        # pass

