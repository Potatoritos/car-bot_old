import io
from typing import Annotated as A
import discord
import requests
import car


class Image(car.Cog):
    category = "Image"

    @car.slash_command_group(name="img")
    async def _(self, ctx): pass

    @car.mixed_command(slash_name="img burning")
    async def burning(self, ctx, text: str):
        """Generates burning text (from cooltext.com)"""
        url = "https://cooltext.com/PostChange"
        data = {
            "LogoID": "4",
            "Text": text,
            "FontSize": "70",
            "Color1_color": "#FF0000",
            "Integer1": "15",
            "Boolean1": "on",
            "Integer9": "0",
            "Integer13": "on",
            "Integer12": "on",
            "BackgroundColor_color": "#FFFFFF"
        }
        await ctx.defer()
        r = requests.post(url, data=data)
        if r.status_code != 200:
            raise car.CommandError("Request failed!")

        # blobyikes
        content = requests.get(r.json()['renderLocation'], verify=False).content
        f = discord.File(io.BytesIO(content), filename="burningtext.gif")

        await ctx.respond(file=f)

