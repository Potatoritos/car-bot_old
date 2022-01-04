from typing import Annotated as A, Optional
import car


class Meta(car.Cog):
    global_category = "Meta"

    @car.text_command()
    async def help(
        self,
        ctx: car.TextContext,
        cmd: A[
            Optional[str],
            "the name of a command"
        ] = None
    ) -> None:
        if cmd is None:
            pass
        else:
            pass

