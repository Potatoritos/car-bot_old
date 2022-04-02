import asyncio
from yt_dlp import YoutubeDL


def dl():
    print('dl')
    opts = {'format': 'bestvideo+bestaudio'}
    with YoutubeDL(opts) as ydl:
        ydl.download(['https://www.youtube.com/watch?v=kTyOKEi8CC4'])
    print('done dl')

dl()


