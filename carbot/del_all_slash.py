import sys
from loguru import logger

import car
import cogs
import config


def main():
    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if config.DEBUG else "INFO")
    bot = car.Bot()

    bot.cog_handler.put_slash_commands(config.APPLICATION_ID, config.TOKEN)

if __name__ == '__main__':
    main()

