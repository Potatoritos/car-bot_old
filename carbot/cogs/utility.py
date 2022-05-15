import asyncio
import os.path
import random
import time
from typing import Annotated as A, Optional

import discord
import yt_dlp

import car


class YTDLLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass


class Utility(car.Cog):
    category = "Utility"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @car.mixed_command(slash_name="pfp", aliases=["avatar", "av"])
    async def pfp(
        self, ctx,
        member: A[
            Optional[discord.Member],
            "if unspecified, displays your pfp"
        ] = None
    ):
        """Displays someone's profile picture (and provides download links)"""
        member = member or ctx.author

        links = [
            (f"[[.{form}]]({member.avatar.replace(format=form).url} "
             f"\"Link to .{form}\")")
            for form in ('webp', 'png', 'jpg')
        ]

        if member.avatar.is_animated():
            links.append(f"[[.gif]]({member.avatar.url} \"Link to .gif\") ")

        link = ' '.join(links)
        e = discord.Embed(description=f"{member.mention}'s avatar\n{link}")
        e.set_image(url=member.avatar.url)

        await ctx.respond(embed=e)

    @car.mixed_command(aliases=["emoji"])
    async def emote(self, ctx, emote: discord.Emoji):
        """Displays a server emote (and provides a download link)"""
        # links = [
            # f"[[.{form}]]({emote.url_as(format=form)} \"Link to .{form}\")"
            # for form in ('webp', 'png', 'jpg')
        # ]
        # if emote.animated:
            # links.append(f"[[.gif]]({emote.url} \"Link to .gif\") ")

        link = f"[[download]]({emote.url})"

        e = discord.Embed(description=f":{emote.name}:\n{link}")
        e.set_image(url=emote.url)
        e.set_footer(text=f"ID: {emote.id}")

        await ctx.respond(embed=e)

    @car.mixed_command()
    async def rand(self, ctx, lower_bound: int, upper_bound: int):
        """Selects a (pseudo)random integer uniformly between an range"""
        n = random.randint(lower_bound, upper_bound)
        await ctx.respond(embed=discord.Embed(description=f":game_die: `{n}`"))

    @car.mixed_command()
    async def choose(
        self, ctx,
        choices: A[str, "comma-seperated choices"],
        n: A[
            Optional[int], car.ToInt() | car.InRange(1, 1000),
            "the amount of choices to select"
        ] = 1
    ):
        """Randomly selects choice(s) from a list, without replacement"""
        choices = [c.strip() for c in choices.split(',')]
        sample = random.sample(choices, min(n, len(choices)))
        result = ' '.join(f"`{s}`" for s in sample)

        if len(result) > 3900:
            raise car.CommandError("I can't fit this in a single message!")

        e = discord.Embed(description=f":game_die: {result}")
        await ctx.respond(embed=e)

    @car.mixed_command(hidden=True)
    @car.requires_clearance(car.ClearanceLevel.TRUSTED)
    async def ytdlp(
        self,
        ctx: car.Context,
        url: A[str, car.ToURL()],
        file_format: A[
            Optional[str],
            "the format of the downloaded file",
            car.FromChoices({'mp4': 'mp4', 'webm': 'webm', 'mp3': 'mp3'})
        ] = 'mp4'
    ):
        """Downloads audio/video with yt-dlp"""
        await ctx.defer()

        file_name = f"dl/ytdlp.{file_format}"
        file_size_bytes: int

        last_update_secs = 0

        def progress_hook(data):
            nonlocal file_size_bytes, last_update_secs
            print(f"PROGRESS HOOK {data['filename']=}, {data['status']=}, {data['total_bytes']=}")
            if data['status'] == 'downloading':
                print(data['tmpfilename'])

                if time.time() - last_update_secs >= 1:
                    # async def send_progress(self):
                        # nonlocal ctx, data
                        # await ctx.

                    if 'estimated_bytes' in data:
                        percentage = data['total_bytes'] / data['estimated_bytes']
                        print(percentage)
                    else:
                        print('wtf')
                    last_update_secs = time.time()
                    # e = discord.Embed(
                        # description=f"`1/3` Downloading... `{percentage:.1f}%`")
                    # asyncio.create_task(
                        # ctx.edit_response(embed=e)
                    # )

            elif data['status'] == 'finished':
                file_size_bytes = data['total_bytes']

        def postprocessor_hook(data):
            print(f"PP HOOK {data['status']=}, {data['postprocessor']=}")

        opts = {
            'format': 'bestaudio+bestvideo',
            'outtmpl': 'dl/ytdlp.%(ext)s',
            'max_filesize': 3e8,
            'logger': YTDLLogger(),
            'progress_hooks': [progress_hook],
            'postprocessor_hooks': [postprocessor_hook]
        }

        def download():
            nonlocal opts, url, file_format
            with yt_dlp.YoutubeDL(opts) as ydl:
                if file_format in ('mp4',):
                    ydl.add_post_processor(
                        yt_dlp.postprocessor.FFmpegVideoConvertorPP(
                            preferedformat=file_format
                        )
                    )
                elif file_format in ('mp3',):
                    # file_format = 'best' if file_format == 'best_audio' \
                        # else file_format

                    ydl.add_post_processor(
                        yt_dlp.postprocessor.FFmpegExtractAudioPP(
                            preferredcodec=file_format
                        )
                    )

                try:
                    a = ydl.download(url)
                except yt_dlp.utils.DownloadError as e:
                    raise car.CommandError(f"Download failed!\n\n```{e}```")
                print(a)

        await asyncio.to_thread(download)

        if file_size_bytes < ctx.upload_limit_bytes:
            await ctx.respond(file=discord.File(file_name, f"ytdlp.{file_format}"))
        else:
            pass

        os.remove(file_name)

