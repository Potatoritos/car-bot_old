import asyncio
import yt_dlp
from yt_dlp import YoutubeDL


def dl():
    print('dl')
    opts = {'format': 'mp4'}
    with YoutubeDL() as ydl:
        url = "https://www.reddit.com/r/worldfunnies/comments/t1n2v6/novo_xite_do_ze_counter_strike_16_xite_de_bomba/"
        url2 = 'https://www.youtube.com/watch?v=kTyOKEi8CC4'
        url3 = 'https://www.youtube.com/watch?v=kTyOKEi8CC4'
        try:
            ydl.download(url3)
        except yt_dlp.utils.DownloadError as e:
            print(e)
            print(str(e))

    print('done dl')

async def main():
    print("main")

    await asyncio.to_thread(dl)

    print("done main")

asyncio.run(main())
print("bonfga69")
