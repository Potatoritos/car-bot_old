import asyncio
import os
import sqlite3
from typing import Annotated as A, Optional, Any

import discord
from gtts import gTTS
from loguru import logger
import mutagen.mp3
import mutagen.wave
import yt_dlp

import car


class CustomAudioSource(discord.AudioSource):
    def __init__(self, source: str, *, start_seconds: float = 0,
                 speed: float = 1, bass_boost: float = 0,
                 treble_boost: float = 0):
        self._start_seconds = start_seconds
        self._speed = speed
        self._bass_boost = bass_boost
        self._treble_boost = treble_boost

        before_opts = None
        if self._start_seconds > 0:
            before_opts = f"-ss {self._start_seconds}"

        opts = ''
        af = []

        if self._speed != 1:
            if self._speed < 0.5:
                # opts = f'-filter:a "atempo=0.5,atempo={2*self._speed}" '
                af.append(f"atempo=0.5,atempo={2*self._speed}")
            elif self._speed <= 2:
                # opts = f'-filter:a "atempo={self._speed}" '
                af.append(f"atempo={self._speed}")
            else:
                # opts = f'-filter:a "atempo=2,atempo={0.5*self._speed}" '
                af.append(f"atempo=2,atempo={0.5*self._speed}")

        if self._bass_boost != 0:
            af.append(f"bass=g={bass_boost}")

        if self._treble_boost != 0:
            af.append(f"treble=g={treble_boost}")

        if af:
            opts += f"-af \"{','.join(af)}\""

        logger.debug(f"Audio source init; {before_opts=}, {opts=}")

        self.audio = discord.FFmpegPCMAudio(source, before_options=before_opts,
                                            options=opts)
        self.count_20ms = 0

    def read(self) -> bytes:
        data = self.audio.read()
        if data:
            self.count_20ms += 1

        return data

    def is_opus(self) -> bool:
        return self.audio.is_opus()

    @property
    def progress_seconds(self) -> float:
        return self._start_seconds + self.count_20ms * 0.02 * self._speed


class SFXSession:
    def __init__(self):
        self._volume = 100.0
        self._speed = 1.0
        self._bass_boost = 0
        self._treble_boost = 0
        self._sound = None
        self._source = None
        self._vc = None
        self._stopped = False

        self.repeat = False
        self.quit_queued = False

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

        if self.vc_is_playing():
            self._vc.source = discord.PCMVolumeTransformer(
                self._source, volume=self._volume*0.01
            )

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, value: float):
        assert 0.25 <= value <= 4
        self._speed = value

        if self.vc_is_playing():
            self.stop()
            self.play(self._sound, start_seconds=self._source.progress_seconds)

    @property
    def bass_boost(self):
        return self.bass_boost

    @bass_boost.setter
    def bass_boost(self, value: float):
        assert -50 <= value <= 50
        self._bass_boost = value

        if self.vc_is_playing():
            self.stop()
            self.play(self._sound, start_seconds=self._source.progress_seconds)

    @property
    def treble_boost(self):
        return self._speed

    @speed.setter
    def treble_boost(self, value: float):
        assert -50 <= value <= 50
        self._treble_boost = value

        if self.vc_is_playing():
            self.stop()
            self.play(self._sound, start_seconds=self._source.progress_seconds)

    @property
    def progress_seconds(self):
        return self._source.progress_seconds

    @property
    def sound(self):
        return self._sound

    @property
    def progress_bar(self) -> str:
        progress_bar = ['─'] * 24
        idx = int(round(self.progress_seconds/self._sound['length'] * 23))
        progress_bar[max(0, min(23, idx))] = '⚪'

        return ''.join(progress_bar)

    @property
    def progress(self) -> str:
        progress_60 = car.s_to_sexagesimal(self.progress_seconds)
        total_60 = car.s_to_sexagesimal(self._sound['length'])
        return f"{progress_60}/{total_60}"

    @property
    def status_desc(self) -> str:
        return (
            f"Playing: `{self.sound['name']}`"
            f"{' :pause_button:' if self.is_paused() else ''}"
            f"{' :repeat:' if self.repeat else ''}\n\n"
            f"{self.progress_bar} {self.progress}\n{self._vc.channel.mention}"
            f" | {self.volume}% volume | {self.speed}x speed "
        )

    def vc_is_playing(self) -> bool:
        return self.vc_has_played() and self._vc.is_playing()

    def vc_has_played(self) -> bool:
        return self.vc_is_connected() and self._sound is not None

    def vc_is_connected(self) -> bool:
        return self._vc is not None and self._vc.is_connected()

    def is_paused(self) -> bool:
        return self._vc.is_paused()

    def pause(self) -> None:
        self._vc.pause()

    def resume(self) -> None:
        self._vc.resume()

    def stop(self) -> None:
        if self.vc_is_playing():
            self._stopped = True
            self._vc.stop()

    def after(self, error) -> None:
        if error:
            return

        if self.repeat and not self._stopped and not self.vc_is_playing():
            logger.debug("Sound effect repeating")
            self.play(self._sound)

    async def join(self, channel):
        if self._vc is not None and self._vc.is_connected():
            await self._vc.disconnect()
        self._vc = await channel.connect()

    async def move(self, channel):
        await self._vc.move_to(channel)

    async def leave(self):
        self.stop()
        await self._vc.disconnect()

    def play(self, sound, *, vc=None, volume=None, repeat=None,
             start_seconds=0, speed=None, bass_boost=None,
             treble_boost=None) -> None:
        self._sound = sound

        if vc is not None:
            self._vc = vc

        if volume is not None:
            self._volume = volume

        if repeat is not None:
            self.repeat = repeat

        if speed is not None:
            self._speed = speed

        if bass_boost is not None:
            self._bass_boost = bass_boost

        if treble_boost is not None:
            self._treble_boost = bass_boost

        if self._vc.is_playing():
            self._vc.stop()

        try:
            self._source = CustomAudioSource(
                self._sound['path'], start_seconds=start_seconds,
                speed=self._speed, bass_boost=self._bass_boost,
                treble_boost=self._treble_boost
            )

        except IOError:
            logger.error(f"Broken sound effect; {self._sound=}")
            raise car.CommandError("This sound effect is broken!")

        self._vc.play(self._source, after=self.after)

        if self._volume != 100:
            self._vc.source = discord.PCMVolumeTransformer(
                self._source, volume=self._volume*0.01)

        self._stopped = False

class Sound(car.Cog):
    category = "Sound"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sessions: dict[int, SFXSession] = {}

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

    @staticmethod
    def free_path(name: str, file_type: str) -> str:
        path = f"./sfx/{name}.{file_type}"

        i = 0
        while os.path.exists(path):
            i += 1
            path = f"./sfx/{name}_{i}.{file_type}"

        return path

    def get_sound(self, name: str, select: str = '*') -> dict[str, Any]:
        sound = self.sfx_list.select(select, 'WHERE name=?', (name.lower(),))
        if len(sound) == 0:
            raise car.ArgumentError("I can't find a sound effect with this "
                                    "name!", 'name')
        return sound

    @car.listener
    async def on_voice_state_update(self, member, before, after):
        voice_state = member.guild.voice_client
        if voice_state is None:
            return

        if member.guild.id not in self.sessions:
            return

        sesh = self.sessions[member.guild.id]

        if len(voice_state.channel.members) == 1:
            sesh.quit_queued = True
            asyncio.create_task(self.queue_quit(sesh))

        elif sesh.quit_queued:
            sesh.quit_queued = False

            if sesh.vc_is_playing():
                sesh.play(sesh.sound, start_seconds=sesh.progress_seconds)

    async def queue_quit(self, sesh):
        count_seconds = 0
        while True:
            if not sesh.quit_queued:
                return

            if count_seconds >= 300:
                await sesh.leave()
                return

            await asyncio.sleep(1)
            count_seconds += 1

    def check_name(self, name: str) -> None:
        if not all(c.isalnum() or c == '_' for c in name):
            raise car.ArgumentError("Names must be alphanumeric! (underscores "
                                    f"allowed)", 'name')

        if len(name) > 24:
            raise car.ArgumentError("Names must ≤ 24 characters long!",
                                    'name')

        if self.sfx_list.select('id', 'WHERE name=?', (name,),
                                flatten=False):
            raise car.ArgumentError("A sound effect with this name already "
                                    "exists!")

    @car.slash_command_group(name="sfx")
    async def _(self, ctx): pass

    sfx_categories = {
        'Songs': 'Songs', 'Clips': 'Clips', 'Sounds': 'Sounds',
        'Ambient': 'Ambient', 'None': 'Uncategorized'
    }

    @car.mixed_command(slash_name="sfx add")
    async def sfxadd(
        self,
        ctx: car.Context,
        name: str,
        category: A[str, car.FromChoices(sfx_categories)]
    ):
        """Adds a sound effect (uses the most recently uploaded file)"""
        name = name.lower()
        self.check_name(name)

        attachment = await ctx.last_attachment()

        supported_formats = ('audio/mp3', 'audio/wav', 'audio/mpeg',
                             'audio/x-wav')

        if attachment.content_type not in supported_formats:
            raise car.CommandError("Sound effects must be in mp3, wav, or mpeg"
                                   " format! (selected file: ``"
                                   f"{car.zwsp_md(attachment.filename)}``)")

        match attachment.content_type:
            case 'audio/mp3' | 'audio/mpeg':
                file_type = 'mp3'
            case 'audio/wav' | 'audio/x-wav':
                file_type = 'wav'
            case _:
                logger.error(f"{attachment.content_type=} not handled!")
                raise ValueError

        path = self.free_path(name, file_type)

        await ctx.defer()

        await attachment.save(path)

        match attachment.content_type:
            case 'audio/mp3' | 'audio/mpeg':
                length = mutagen.mp3.MP3(path).info.length
            case 'audio/wav' | 'audio/x-wav':
                length = mutagen.wave.WAVE(path).info.length
            case _:
                logger.error(f"{attachment.content_type=} not handled!")
                raise ValueError

        if length < 0.1:
            raise car.CommandError("Sound effect length must be >= 0.1s!")

        self.sfx_list.insert(id=None, name=name, category=category, path=path,
                             length=length, user_id=ctx.author.id,
                             verified=False)
        logger.debug(f"Sound effect added: {name=}, {category=}, {path=}")

        e = discord.Embed(description=f"Sound effect `{name}` added!")
        await ctx.respond(embed=e)

    @car.mixed_command(slash_name="sfx addyt")
    async def sfxaddyt(
        self, ctx,
        name: str,
        category: A[str, car.FromChoices(sfx_categories)],
        url: A[str, "the URL of the youtube video to download"]
    ):
        """Adds a sound effect (uses a youtube link)"""
        if not url.startswith("https://") and not url.startswith('http://'):
            url = "https://" + url

        if not url.startswith("https://www.youtube.com/watch?v=") \
                or len(url) > 105:
            raise car.ArgumentError("Invalid youtube link!", 'url')

        self.check_name(name)

        path = self.free_path(name, 'mp3')

        i = 0
        while os.path.exists(path):
            i += 1
            path = f"./sfx/{name}_{i}.mp3"

        opts = {
            'format': 'bestaudio',
            'outtmpl': path,
            'max_filesize': 3e8
        }

        def download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.add_post_processor(
                    yt_dlp.postprocessor.FFmpegExtractAudioPP(
                        preferredcodec='mp3'
                    )
                )
                
                try:
                    a = ydl.download(url)
                except yt_dlp.utils.DownloadError as e:
                    raise car.CommandError(f"Download failed!\n\n```{e}```")

        await ctx.defer()

        await asyncio.to_thread(download)

        length = mutagen.mp3.MP3(path).info.length

        self.sfx_list.insert(id=None, name=name, category=category, path=path,
                             length=length, user_id=ctx.author.id,
                             verified=False)
        logger.debug(f"Sound effect added (yt): {name=}, {category=}, {path=}")

        e = discord.Embed(description=f"Sound effect `{name}` added!")
        await ctx.respond(embed=e)

    @car.mixed_command(slash_name="sfx list")
    async def sfxlist(
        self, ctx,
        added_by: Optional[discord.Member] = None,
        show_durations: Optional[bool] = False
    ):
        """Lists all sound effects"""

        categories = {}

        if show_durations:
            to_select = 'name, category, length'
        else:
            to_select = 'name, category'

        if added_by is not None:
            lst = self.sfx_list.select(to_select,
                                       'WHERE user_id=? ORDER BY NAME',
                                       (added_by.id,), flatten=False)
        else:
            lst = self.sfx_list.select(to_select, 'ORDER BY name',
                                       flatten=False)

        for sound in lst:
            cat = sound['category']

            if cat not in categories:
                categories[cat] = []

            name = sound['name']
            if show_durations:
                name += f"[{car.s_to_sexagesimal(sound['length'])}]"

            categories[cat].append(name)

        e = discord.Embed(title="Sound effect list")

        if added_by:
            e.description = "Displaying sound effects added by " \
                + added_by.mention

        for k, v in categories.items():
            e.add_field(name=k, value=' '.join(f"`{n}`" for n in v),
                        inline=False)

        if len(categories) == 0:
            if added_by:
                e.description += "\n\n*No sound effects found*"
            else:
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
        repeat: Optional[bool] = False,
        volume: A[Optional[float], car.ToFloat() | car.InRange(0, 200)] = None,
        speed: A[Optional[float], car.ToFloat() | car.InRange(0.25, 4)] = None,
        bass_boost: A[
            Optional[float], car.ToFloat() | car.InRange(-50, 50)
        ] = None,
        treble_boost: A[
            Optional[float], car.ToFloat() | car.InRange(-50, 50)
        ] = None,
        start_time: A[Optional[float], car.ToSeconds()] = 0,
        join_vc: A[
            Optional[bool],
            "specifies whether I should join your vc"
        ] = True
    ):
        """Plays a sound effect"""

        if ctx.author.voice is None and join_vc:
            raise car.CommandError("You must be in a voice channel!")

        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc is None or not vc.is_connected():
            if not join_vc:
                raise car.CommandError("I'm not in a voice channel!")

            vc = await ctx.author.voice.channel.connect()

        if join_vc and vc.channel != ctx.author.voice.channel:
            await vc.disconnect()
            vc = await ctx.author.voice.channel.connect()

        sound = self.get_sound(name)

        if ctx.guild.id not in self.sessions:
            self.sessions[ctx.guild.id] = SFXSession()

        sesh = self.sessions[ctx.guild.id]

        sesh.play(sound, vc=vc, volume=volume, repeat=repeat, speed=speed,
                  start_seconds=start_time, bass_boost=bass_boost,
                  treble_boost=treble_boost)

        desc = (
            f":musical_note: Playing sound: `{name}` [volume: {sesh.volume}%] "
            f"[speed: {sesh.speed}x]"
        )
        if repeat:
            desc += " [repeating]"
        await ctx.respond(embed=discord.Embed(description=desc))

    tts_languages = {
        "Arabic": 'ar',
        "English (AU)": 'en:com.au',
        "English (US)": 'en',
        "English (UK)": 'en:co.uk',
        "English (IN)": 'en:co.in',
        "French (CA)": 'fr:ca',
        "French (FR)": 'fr',
        "German": 'de',
        "Greek": 'el',
        "Hebrew": 'iw',
        "Hindi": 'hi',
        "Italian": 'it',
        "Japanese": 'ja',
        "Korean": 'ko',
        "Latin": 'la',
        "Russian": 'ru',
        "Mandarin (CN)": 'zh-CN',
        "Mandarin (TW)": 'zh-TW',
        "Norwegian": 'no',
        "Spanish (MX)": 'es:com.mx',
        "Spanish (ES)": 'es',
        "Swedish": 'sv',
        "Thai": 'th',
        "Ukranian": 'uk',
        "Vietnamese": 'vi'
    }

    @car.mixed_command(slash_name="sfx addtts", aliases=["addtts"])
    async def sfxaddtts(
        self, ctx,
        name: str,
        category: A[str, car.FromChoices(sfx_categories)],
        text: str,
        language: A[
            Optional[str],
            car.FromChoices(tts_languages)
        ] = 'en',
    ):
        """Adds text-to-speech to the sound effect list"""
        path = self.free_path(name, 'mp3')

        def generate_tts():
            spl = language.split(':')

            kwargs = {'lang': spl[0]}
            if len(spl) > 1:
                kwargs['tld'] = spl[1]

            gTTS(text, **kwargs).save(path)

        await ctx.defer()

        await asyncio.to_thread(generate_tts)

        length = mutagen.mp3.MP3(path).info.length

        self.sfx_list.insert(id=None, name=name, category=category, path=path,
                             length=length, user_id=ctx.author.id,
                             verified=False)
        logger.debug(
            f"Sound effect added (tts): {name=}, {category=}, {path=}")

        e = discord.Embed(description=f"Sound effect `{name}` added!")
        await ctx.respond(embed=e)

    @car.mixed_command(slash_name="sfx tts", aliases=["sfxtts"])
    async def tts(
        self, ctx,
        text: str,
        language: A[
            Optional[str],
            car.FromChoices(tts_languages)
        ] = 'en',
        repeat: Optional[bool] = False,
        volume: A[Optional[float], car.ToFloat() | car.InRange(0, 200)] = None,
        speed: A[Optional[float], car.ToFloat() | car.InRange(0.25, 4)] = None,
        upload: A[
            Optional[bool],
            "if specified, just uploads the tts (does not work with vol/speed)"
        ] = False,
        join_vc: A[
            Optional[bool],
            "specifies whether I should join your vc"
        ] = True
    ):
        """Plays text-to-speech in a voice channel"""

        if not upload:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc is None or not vc.is_connected():
                if not join_vc:
                    raise car.CommandError("I must be in a voice channel!")

                vc = await ctx.author.voice.channel.connect()

            if join_vc and vc.channel != ctx.author.voice.channel:
                await vc.disconnect()
                vc = await ctx.author.voice.channel.connect()

        path = "./sfx/tts.mp3"

        def generate_tts():
            spl = language.split(':')

            kwargs = {'lang': spl[0]}
            if len(spl) > 1:
                kwargs['tld'] = spl[1]

            gTTS(text, **kwargs).save(path)

        await ctx.defer()

        await asyncio.to_thread(generate_tts)

        if upload:
            await ctx.respond(file=discord.File(path))
            return

        length = mutagen.mp3.MP3(path).info.length

        if ctx.guild.id not in self.sessions:
            self.sessions[ctx.guild.id] = SFXSession()

        sesh = self.sessions[ctx.guild.id]

        sound = {
            'id': 99999999,
            'name': "[tts]",
            'category': "Uncategorized",
            'path': "./sfx/tts.mp3",
            'length': length,
            'user_id': ctx.author.id,
            'verified': False
        }

        sesh.play(sound, vc=vc, volume=volume, repeat=repeat, speed=speed)

        desc = (
            f":musical_note: Playing TTS [volume: {sesh.volume}%] "
            f"[speed: {sesh.speed}x]"
        )
        if repeat:
            desc += " [repeating]"
        await ctx.respond(embed=discord.Embed(description=desc))

    @car.mixed_command(slash_name="sfx volume", aliases=["sfxvol"])
    async def sfxvolume(self, ctx,
                        volume: A[float, car.ToFloat() | car.InRange(0, 200)]):
        """Sets audio volume"""
        if ctx.guild.id not in self.sessions:
            self.sessions[ctx.guild.id] = SFXSession()

        self.sessions[ctx.guild.id].volume = volume

        e = discord.Embed(
            description=f":musical_note: Volume set to {volume}%!")
        await ctx.respond(embed=e)

    @car.mixed_command(slash_name="sfx bassboost")
    async def sfxbassboost(self, ctx,
                       boost: A[float, car.ToFloat() | car.InRange(-50, 50)]):
        """Sets audio bass boost"""
        if ctx.guild.id not in self.sessions:
            self.sessions[ctx.guild.id] = SFXSession()

        self.sessions[ctx.guild.id].bass_boost = boost

        e = discord.Embed(
            description=f":musical_note: Set bass boost to {boost}!")
        await ctx.respond(embed=e)

    @car.mixed_command(slash_name="sfx trebleboost")
    async def sfxtrebleboost(self, ctx,
                       boost: A[float, car.ToFloat() | car.InRange(-50, 50)]):
        """Sets audio treble boost"""
        if ctx.guild.id not in self.sessions:
            self.sessions[ctx.guild.id] = SFXSession()

        self.sessions[ctx.guild.id].treble_boost = boost

        e = discord.Embed(
            description=f":musical_note: Set treble boost to {boost}!")
        await ctx.respond(embed=e)

    @car.mixed_command(slash_name="sfx speed")
    async def sfxspeed(self, ctx,
                       speed: A[float, car.ToFloat() | car.InRange(0.25, 4)]):
        """Sets audio playback speed"""
        if ctx.guild.id not in self.sessions:
            self.sessions[ctx.guild.id] = SFXSession()

        self.sessions[ctx.guild.id].speed = speed

        e = discord.Embed(description=f":musical_note: Speed set to {speed}x!")
        await ctx.respond(embed=e)

    @car.mixed_command(slash_name="sfx seek")
    async def sfxseek(self, ctx, timestamp: A[float, car.ToSeconds()]):
        """Skips to a timestamp"""
        if ctx.guild.id not in self.sessions \
                or not self.sessions[ctx.guild.id].vc_has_played():
            raise car.CommandError("I'm not playing anything right now!")

        sesh = self.sessions[ctx.guild.id]

        length = sesh.sound['length']

        timestamp_60 = car.s_to_sexagesimal(timestamp)
        total_60 = car.s_to_sexagesimal(length)

        if timestamp > length:
            raise car.ArgumentError(
                f"This timestamp ({timestamp_60}) must be less than the "
                f"sound effect's duration ({total_60})!"
            )

        sesh.play(sesh.sound, start_seconds=timestamp)

        desc = ":musical_note: Sought!\n\n" + sesh.status_desc
        await ctx.respond(embed=discord.Embed(description=desc))

    @car.mixed_command(slash_name="sfx status")
    async def sfxstatus(self, ctx):
        """Displays the currently playing sound effect's status"""
        if ctx.guild.id not in self.sessions \
                or not self.sessions[ctx.guild.id].vc_has_played():
            raise car.CommandError("I'm not playing anything right now!")

        desc = f":musical_note: " + self.sessions[ctx.guild.id].status_desc
        await ctx.respond(embed=discord.Embed(description=desc))

    @car.mixed_command(slash_name="sfx stop")
    async def sfxstop(self, ctx):
        """Stops the currently playing sound effect"""
        if ctx.guild.id not in self.sessions \
                or not self.sessions[ctx.guild.id].vc_is_playing():
            raise car.CommandError("I'm not playing anything right now!")

        self.sessions[ctx.guild.id].stop()

        e = discord.Embed(description=":musical_note: Stopped!")
        await ctx.respond(embed=e)

    @car.mixed_command(slash_name="sfx repeat")
    async def sfxrepeat(self, ctx):
        """Toggles whether the currently playing sound effect should repeat"""
        if ctx.guild.id not in self.sessions \
                or not self.sessions[ctx.guild.id].vc_is_playing():
            raise car.CommandError("I'm not playing anything right now!")

        sesh = self.sessions[ctx.guild.id]
        sesh.repeat = not sesh.repeat

        if sesh.repeat:
            desc = ":musical_note: Repeating!"
        else:
            desc = ":musical_note: No longer repeating!"

        desc += "\n\n" + sesh.status_desc

        e = discord.Embed(description=desc)
        await ctx.respond(embed=e)

    @car.mixed_command(slash_name="sfx resume", aliases=["sfxunpause"])
    async def sfxresume(self, ctx):
        """Resumes the currently paused sound"""
        if ctx.guild.id not in self.sessions \
                or not self.sessions[ctx.guild.id].vc_has_played():
            raise car.CommandError("I'm not playing anything right now!")

        sesh = self.sessions[ctx.guild.id]
        if not sesh.is_paused():
            raise car.CommandError("I'm already playing!")

        sesh.resume()

        desc = ":musical_note: Resumed!\n\n" + sesh.status_desc
        await ctx.respond(embed=discord.Embed(description=desc))

    @car.mixed_command(slash_name="sfx pause")
    async def sfxpause(self, ctx):
        """Pauses the currently playing sound"""
        if ctx.guild.id not in self.sessions \
                or not self.sessions[ctx.guild.id].vc_has_played():
            raise car.CommandError("I'm not playing anything right now!")

        sesh = self.sessions[ctx.guild.id]
        if sesh.is_paused():
            raise car.CommandError("I'm already paused!")

        sesh.pause()

        desc = ":musical_note: Paused!\n\n" + sesh.status_desc
        await ctx.respond(embed=discord.Embed(description=desc))

    @car.mixed_command(slash_name="sfx join", aliases=["sfxmove"])
    async def sfxjoin(
        self, ctx,
        channel: A[
            Optional[discord.VoiceChannel],
            "the voice channel to move to. If unspecified, joins your VC"
        ] = None
    ):
        """Joins or moves to a voice channel"""
        if channel is None:
            if ctx.author.voice is None:
                raise car.CommandError("You must specify a voice channel "
                                       "or be in one!")

            channel = ctx.author.voice.channel

        if ctx.guild.id not in self.sessions:
            self.sessions[ctx.guild.id] = SFXSession()

        sesh = self.sessions[ctx.guild.id]
        if sesh.vc_is_playing():
            await sesh.move(channel)
        else:
            await sesh.join(channel)

        e = discord.Embed(description=f"Joined {channel.mention}!")
        await ctx.respond(embed=e)

    @car.mixed_command(slash_name="sfx leave", aliases=["sfxquit"])
    async def sfxleave(self, ctx):
        """Leaves the voice channel"""
        if ctx.guild.id not in self.sessions \
                or not self.sessions[ctx.guild.id].vc_is_connected():
            raise car.CommandError("I'm not connected to a voice channel!")

        sesh = self.sessions[ctx.guild.id]

        await sesh.leave()

        e = discord.Embed(description="Left the voice channel!")
        await ctx.respond(embed=e)

    @car.text_command(hidden=True)
    @car.requires_clearance(car.ClearanceLevel.ADMIN)
    async def sfxmanuadd(self, ctx, name: str, category: str, path: str,
                         user_id: Optional[int] = None):
        """Manually adds a sound effect"""
        match path.split('.')[-1]:
            case 'mp3':
                length = mutagen.mp3.MP3(path).info.length
            case 'wav':
                length = mutagen.wave.WAVE(path).info.length
            case _:
                logger.error(f"{attachment.content_type=} not handled!")
                raise ValueError

        self.sfx_list.insert(id=None, name=name, category=category, path=path,
                             length=length, user_id=user_id or ctx.author.id,
                             verified=False)

        logger.info(f"sfx manually added: {name=}, {category=}, {path=}")
        await ctx.respond(f"added: {name=}, {category=}, {path=}")

