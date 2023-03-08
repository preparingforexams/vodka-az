import logging

from az.bot import AzBot
from az.init import initialize

_LOG = logging.getLogger(__package__)

if __name__ == "__main__":
    config = initialize()
    bot = AzBot(config)
    _LOG.info("Running bot")
    bot.run()
