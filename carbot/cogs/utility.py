import asyncio
import os.path
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

    @car.mixed_command(max_concurrency=1)
    async def ytdlp(
        self,
        ctx: car.Context,
        url: A[str, "the URL of the video to download"],
        file_format: A[
            Optional[str],
            "the format of the downloaded file",
            car.FromChoices({'mp4': 'mp4', 'webm': 'webm'})
        ] = 'mp4'
    ):
        """Downloads audio/video with yt-dlp"""
        if ' ' in url or '"' in url:
            raise ArgumentError("Invalid URL!")
        await ctx.defer()

        file_name = self.temp_filename(file_format)

        output_file_name: str
        file_size_bytes: int

        def progress_hook(data):
            nonlocal output_file_name, file_size_bytes
            print(f"PROGRESS HOOK {data['filename']=}, {data['status']=}, {data['total_bytes']=}")
            if data['status'] == 'downloading':
                pass
            elif data['status'] == 'finished':
                output_file_name = data['filename']
                file_size_bytes = data['total_bytes']

        def postprocessor_hook(data):
            print(f"PP HOOK {data['status']=}")

        opts = {
            'format': file_format,
            'outtmpl': file_name,
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
                    file_format = 'best' if file_format == 'best_audio' \
                        else file_format

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

        upload_limits_bytes = [8e6, 8e6, 5e7, 1e8]

        if file_size_bytes < upload_limits_bytes[ctx.guild.premium_tier]:
            await ctx.respond(file=discord.File(output_file_name, "ytdlp.mp4"))
        else:
            pass

        os.remove(file_name)

