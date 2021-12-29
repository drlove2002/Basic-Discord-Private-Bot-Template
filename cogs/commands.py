from nextcord.ext.commands import Cog

from utils import logging
from core.bot import MainBot

logger = logging.get_logger(__name__)


class Commands(Cog):

    def __init__(self, bot: MainBot):
        self.bot = bot

    # template


def setup(bot: MainBot):
    bot.add_cog(Commands(bot))
