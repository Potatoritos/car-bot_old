import asyncio
from typing import Annotated as A, Optional
import discord
from loguru import logger

import car


class TestCog(car.Cog):
    category = "test category"
    checks = ()

    @car.slash_command_group(name="a")
    async def a(self, ctx):
        print("cmda")

    @car.slash_command(name="a b")
    async def a_b(self, ctx):
        pass

    @car.slash_command_group(name="a c")
    async def a_c(self, ctx):
        pass

    @car.slash_command(name="a c a")
    async def a_c_a(self, ctx):
        pass

    @car.slash_command(name="a c b")
    async def a_c_b(self, ctx):
        pass

    @car.slash_command(name="a c c")
    async def a_c_c(
        self,
        ctx,
        a: A[int, car.InRange(-2, 5)],
        b: A[str, car.FromChoices({"Value A": "val_a",
                                   "Value B": "val_b",
                                   "Value C": "val_c"})],
        c: bool,
        d: discord.Member,
        e: discord.Role,
        f: discord.TextChannel
    ):
        """
        Line 1
        Line 2
        Line 3
        """
        logger.debug(f"a: {a}\n b: {b}\n c: {c}\n d: {d}\n e: {e}\n f: {f}")

    @car.mixed_command(text_name="b", slash_name="b")
    async def b(self, ctx):
        await ctx.respond("waiting for 4 seconds...")
        await asyncio.sleep(1)
        await ctx.edit_response(content="waiting for 3 seconds...")
        await asyncio.sleep(1)
        await ctx.edit_response(content="waiting for 2 seconds...")
        await asyncio.sleep(1)
        await ctx.edit_response(content="waiting for 1 seconds...")
        await asyncio.sleep(1)
        await ctx.edit_response(content="done")

    @car.mixed_command(text_name="boing", slash_name="boing")
    @car.requires_permissions(administrator=True)
    @car.guild_must_be_id(495327409487478785)
    async def boing(
        self,
        ctx,
        arg1: A[int, "bing bong", car.InRange(lower=-3)],
        arg2: str,
        arg3: A[float, "this is a description", car.FromChoices({"a":2.3, "b":6.9, "c":-2})],
        arg4: A[bool, "asdasd *sdfsdf*"],
        arg5: A[Optional[float], "asdsk gfjglkdgj", car.InRange(upper=72.7)] = 69
    ):
        """Command description here"""
        logger.debug(ctx.args)

    @car.text_command()
    async def user(self, ctx, u: discord.Member):
        await ctx.send(f"{u.name}#{u.discriminator} {u.mention}")

    @car.text_command()
    async def role(self, ctx, r: discord.Role):
        await ctx.send(f"{r.mention}")

    @car.text_command()
    async def text_channel(self, ctx, c: discord.TextChannel):
        await ctx.send(f"{c.mention}")

    @car.text_command()
    async def ping_everyone(self, ctx):
        await ctx.send("@everyone")

    @car.mixed_command(text_name="admintest", slash_name="admintest")
    @car.requires_permissions(administrator=True)
    async def admintest(self, ctx):
        await ctx.respond("yes")

    @car.mixed_command(text_name="permtest", slash_name="permtest")
    @car.requires_permissions(attach_files=True)
    async def permtest(self, ctx):
        await ctx.respond("yes")

    @car.slash_command_group(name="breaktest")
    async def breaktest(self, ctx): pass

    @car.slash_command_group(name="breaktest breaktest2")
    async def breaktest2(self, ctx): pass

    @car.slash_command(name="breaktest breaktest2 breaktest3")
    async def breaktest3(self, ctx): pass

    @car.slash_command(name="breaktest breaktest2 breaktest4")
    async def breaktest4(self, ctx): pass

    @car.slash_command(name="breaktest breaktest2 breaktest5")
    async def breaktest5(self, ctx): pass

    @car.slash_command(name="breaktest breaktest2 breaktest6")
    async def breaktest6(self, ctx): pass

