from nextcord.ext.commands import Cog, Context

from core.bot import MainBot
from core.constants import COMMAND_CHANNELS
from core.help import EmbedHelpCommand
from utils import logging
from utils.util import Raise

logger = logging.get_logger(__name__)


class Help(Cog, name="Help command"):
    """Displays help information for commands and cogs"""

    def __init__(self, bot: MainBot):
        self.__bot = bot
        self.__original_help_command = bot.help_command
        bot.help_command = EmbedHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.__bot.help_command = self.__original_help_command

    @Cog.listener()
    async def on_ready(self):
        logger.info(f"{self.__class__.__name__} Cog has been loaded")
        logger.line()

    async def cog_check(self, ctx: Context):
        if ctx.channel.id not in COMMAND_CHANNELS:
            await Raise(ctx, "Help command only usable in command channels").info()
            return False
        return True


# setup functions for bot
def setup(bot: MainBot):
    bot.add_cog(Help(bot))
