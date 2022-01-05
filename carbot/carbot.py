import sys
from loguru import logger

import car
import cogs
import config


def main():
    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if config.DEBUG else "INFO")
    bot = car.Bot()

    for cog_cls in (
        cogs.TestCog,
        cogs.Meta
    ):
        bot.cog_handler.add_cog_class(cog_cls)

    for cog_name in (
        "TestCog",
        "Meta"
    ):
        bot.cog_handler.load_cog(cog_name)

    # bot.cog_handler.put_slash_commands()
    bot.run(config.TOKEN)

if __name__ == '__main__':
    main()

