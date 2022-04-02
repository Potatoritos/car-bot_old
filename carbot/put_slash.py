import sys
from loguru import logger

import car
import cogs
import config


def main():
    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if config.DEBUG else "INFO")
    bot = car.Bot()

    for cog_cls in config.cogs_to_load:
        bot.cog_handler.add_cog_class(cog_cls)
        bot.cog_handler.load_cog(cog_cls.__name__)

    bot.cog_handler.put_slash_commands(config.APPLICATION_ID, config.TOKEN)

if __name__ == '__main__':
    main()

