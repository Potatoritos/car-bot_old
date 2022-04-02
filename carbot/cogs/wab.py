from typing import Annotated as A, Optional
import discord
import car


class Wab(car.Cog):
    category = "Wab"

    @car.listener
    async def on_message(self, msg):
        if msg.author.id == 852247774325243963 or msg.author.id == 153240776216805376:
            tok = car.Tokenizer(msg.content)

            ctx = car.TextContext.from_message(self.bot, msg)

            pings = [(await car.convert(ctx, p[5:], discord.Member)).mention
                     for p in tok.tokens()
                     if p.startswith("ping:") and len(p) > 5]

            if pings:
                allowed = discord.AllowedMentions(everyone=False, users=True,
                                                  roles=False)
                await ctx.reply(' '.join(pings), allowed_mentions=allowed)
