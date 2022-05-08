import os
import sqlite3
from typing import Annotated as A, Optional, Any

import discord
from loguru import logger

import car


class AudioSourceTracked(discord.AudioSource):
    def __init__(self, source):
        self._source = source
        self.count_20ms = 0

    def read(self) -> bytes:
        data = self._source.read()
        if data:
            self.count_20ms += 1

    @property
    def progress_seconds(self) -> float:
        return self.count_20ms * 0.02


class SFXSession:
    def __init__(self):
        pass


class Sound(car.Cog):
    category = "Sound"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sfx_list = car.DBTable(self.bot.con, 'sfx_list', (
            car.DBColumn('id', 0, is_primary=True),
            car.DBColumn('name', "", is_unique=True),
            car.DBColumn('category', "Uncategorized"),
            car.DBColumn('path', ""),
            car.DBColumn('length', 0.0),
            car.DBColumn('user_id', 0),
            car.DBColumn('verified', False)
        ))

        self.playlists = car.DBTable(self.bot.con, 'sfx_playlists', (
            car.DBColumn('id', 0, is_primary=True),
            car.DBColumn('name', "", is_unique=True),
            car.DBColumn('sfx', []),
            car.DBColumn('length', 0.0),
            car.DBColumn('user_id', 0),
            car.DBColumn('verified', False)
        ))

    def get_sound(self, name: str) -> dict[str, Any]:
        sound = self.sfx_list.select('*', 'WHERE name=?', (name.lower(),))
        if len(sound) == 0:
            raise car.ArgumentError("I can't find a sound effect with this "
                                    "name!", 'name')
        return sound

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
        name = name.lower()
        if not all(c.isalnum() or c == '_' for c in name):
            raise car.ArgumentError("Names must be alphanumeric! (underscores "
                                    f"allowed)", 'name')

        if len(name) > 24:
            raise car.ArgumentError("Names must ≤ 24 characters long!",
                                    'name')

        attachment = await ctx.last_attachment()

        if not attachment.content_type in ('audio/mp3', 'audio/wav'):
            pass

        if not attachment.content_type.startswith('audio') and \
                not attachment.content_type.startswith('video'):
            raise car.CommandError(f"``{car.zwsp_md(attachment.filename)}`` "
                                   "does not seem to be an audio file!")

        file_type = attachment.filename.split('.')[-1]


        path = f'./sfx/{name}.{file_type}'

        i = 0
        while os.path.exists(path):
            i += 1
            path = f"./sfx/{name}_{i}.{file_type}"

        if self.sfx_list.select('id', 'WHERE name=?', (name,),
                                flatten=False):
            raise car.ArgumentError("A sound effect with this name already "
                                    "exists!")

        await attachment.save(path)

        self.sfx_list.insert(None, name, category, path, ctx.author.id, False)
        logger.debug(f"Sound effect saved: {name=}, {category=}, {path=}")

        await ctx.respond(f"Sound effect `{name}` added!")

    @car.mixed_command(slash_name="sfx list")
    async def sfxlist(
        self, ctx,
        added_by: Optional[discord.Member] = None,
        show_durations: Optional[bool] = False
    ):
        """Lists all sound effects"""

        categories = {}

        if added_by is not None:
            lst = self.sfx_list.select('name, category',
                                       'WHERE user_id=? ORDER BY NAME',
                                       (added_by.id,))
        else:
            lst = self.sfx_list.select('name, category', 'ORDER BY name')

        for sound in lst:
            cat = sound['category']

            if cat not in categories:
                categories[cat] = []

            name = sound['name']
            if show_durations:
                name += f"[{car.s_to_sexagesimal(sound['duration'])}]"

            categories[cat].append(name)

        e = discord.Embed(title="Sound effect list")

        for k, v in categories.items():
            e.add_field(name=k, value=' '.join(f"`{n}`" for n in v),
                        inline=False)

        if len(categories) == 0:
            e.description = "*No sound effects found*"

        await ctx.respond(embed=e)

    @car.mixed_command(slash_name="sfx remove", aliases=["sfxdelete"])
    async def sfxremove(self, ctx, name: str):
        """Removes a sound effect"""
        sound = self.get_sound(name)

        if ctx.author.id != sound['user_id']:
            try:
                car.RequiresClearance(car.ClearanceLevel.TRUSTED).check()
            except:
                raise car.CommandError("You aren't allowed to remove other "
                                       "people's sound effects! (this one was "
                                       f"submitted by <@{sound['user_id']}>")

        self.sfx_list.delete('WHERE id=?', (sound['id'],))

        try:
            os.remove(sound['path'])
        except FileNotFoundError:
            logger.error(f"File '{sound['path']}' not found! {sound=}")

        e = discord.Embed(description=f"Removed sound effect `{name}`!")
        await ctx.respond(embed=e)

    @car.mixed_command(slash_name="sfx edit", aliases=["sfxmodify"])
    async def sfxedit(
        self, ctx,
        name: str,
        new_name: Optional[str] = None,
        new_category: A[Optional[str], car.FromChoices({
            'Songs': 'Songs', 'Clips': 'Clips', 'Sounds': 'Sounds',
            'Ambient': 'Ambient', 'None': 'Uncategorized'
        })] = None
    ):
        """Changes the details of a sound effect"""
        sound = self.get_sound(name)

        if ctx.author.id != sound['user_id']:
            try:
                car.RequiresClearance(car.ClearanceLevel.TRUSTED).check()
            except:
                raise car.CommandError("You aren't allowed to edit other "
                                       "people's sound effects! (this one was "
                                       f"submitted by <@{sound['user_id']}>)")
        updates = {}
        desc = "Updated sound effect!\n"

        if new_name is not None:
            updates['name'] = new_name
            desc += f"\nName: `{name}` ➜ **`{new_name}`**"
        else:
            desc += f"\nName: `{name}`"

        if new_category is not None:
            updates['category'] = new_category
            desc += (f"\nCategory: `{sound['category']}` ➜ "
                     f"**`{new_category}`**")
        else:
            desc += f"\nCategory: `{sound['category']}`"

        if len(updates) == 0:
            raise car.CommandError("Edits not specified! (give a value for"
                                   "`new_name` or `new_category`)")

        self.sfx_list.update(sound['id'], **updates)

        await ctx.respond(embed=discord.Embed(description=desc))

    @car.mixed_command(slash_name="sfx play", aliases=["sfxplay"])
    async def sfx(
        self, ctx,
        name: A[str, "the name of the sound effect to play (use `sfx list` "
                "to view all names)"],
        volume: A[Optional[int], car.ToInt() | car.InRange(0, 200)] = 100
    ):
        """Plays a sound effect"""

        if ctx.author.voice is None:
            raise car.CommandError("You must be in a voice channel!")

        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc is None or not vc.is_connected():
            vc = await ctx.author.voice.channel.connect()

        sound = self.get_sound(name)

        if vc.is_playing():
            vc.stop()

        try:
            vc.play(discord.FFmpegPCMAudio(sound['path']))
            vc.source = discord.PCMVolumeTransformer(vc.source, volume=volume*0.01)
        except IOError:
            raise car.CommandError("This sound effect is broken!")

        await ctx.respond(embed=discord.Embed(
            description=f"Playing sound: `{name}`"))

    @car.mixed_command(slash_name="sfx volume", aliases=["sfxvol"])
    async def sfxvolume(self, ctx,
                        volume: A[int, car.ToInt() | car.InRange(0, 200)]):
        """Sets the volume of the currently playing sound effect"""

        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc is None or not vc.is_connected() or not vc.is_playing():
            raise car.CommandError("I'm not playing any sound effect!")

        vc.source.volume = volume * 0.01

        await ctx.respond(embed=discord.Embed(
            description=f"Volume set to {volume}%"))

    @car.mixed_command(slash_name="sfx seek")
    async def sfxseek(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc is None or not vc.is_connected() or not vc.is_playing():
            raise car.CommandError("I'm not playing any sound effect!")

        vc.play()

    # @car.mixed_command(text_name="sfx", slash_name="sfx play",
                       # aliases=["sfxplay"])
    # async def sfxplay(self, ctx):
        # pass

    # @car.mixed_command(slash_name="sfx join")
    # async def sfxjoin(self, ctx):
        # pass

