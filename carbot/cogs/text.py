from typing import Annotated as A, Optional
import discord
import car
import cowsay


class Text(car.Cog):
    category = "Text"
    @car.mixed_command()
    async def cowsay(
        self,
        ctx: car.Context,
        text: str,
        character: A[
            Optional[str],
            car.FromChoices({
                'Cow': "cow",
                'Tux': "tux"
            }),
        ] = "cow"
    ):
        text = car.zwsp(cowsay.get_output_string(character, text), '`')
        await ctx.respond(f"```{text}```")

