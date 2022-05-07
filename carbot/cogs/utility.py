import asyncio
import os.path
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
        self.taken_indices: set[int] = set()

    def temp_filename(self, ext: str) -> str:
        i = 0
        while i := i+1:
            name = f"dl/ytdlp_{i}.{ext}"
            if not os.path.exists(name) and not i in self.taken_indices:
                self.taken_indices.add(i)
                return name

    @car.mixed_command()
    async def print(self, ctx: car.Context, text: str):
        """b13i5n"""
        print(text)
        await ctx.respond('a')

    @car.mixed_command(max_concurrency=1)
    async def ytdlp(
        self,
        ctx: car.Context,
        url: A[str, car.ToURL(allowed_sites=car.YTDL_ALLOWED_SITES)],
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

