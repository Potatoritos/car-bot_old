import discord
from loguru import logger

import car


class Admin(car.Cog):
    category = "Admin"
    checks = (car.requires_clearance(car.ClearanceLevel.ADMIN),)

    @car.text_command(hidden=True)
    async def set_clearance(self, ctx, user_id: int, level: int):
        self.bot.user_admin.insert(user_id=user_id, clearance=level)

        logger.info(f"Clearance level of {user_id} set to {level}")
        await ctx.respond(f"Clearance level of `{user_id}` set to `{level}`")

    @car.text_command(hidden=True)
    async def stop(self, ctx):
        logger.info("Stop command invoked")
        await self.bot.close()
        sys.exit()

