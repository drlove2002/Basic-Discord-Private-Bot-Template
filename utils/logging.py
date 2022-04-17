import logging
import sys
from typing import TYPE_CHECKING, Optional
from nextcord.utils import find
from nextcord import Embed, ClientException, Color
from colorama import Fore, Style

if TYPE_CHECKING:
    from core.bot import BaseMainBot
    from nextcord import Webhook


class Log:
    def __init__(self, bot: "BaseMainBot"):
        self._bot = bot
        self.__webhook: Optional["Webhook"] = None

    async def sync(self, _id: int) -> "Webhook":
        channel = self._bot.guild.get_channel(_id)
        self.__webhook = find(lambda wh: wh.user.id == self._bot.user.id, (await channel.webhooks()))
        if self.__webhook is None:
            self.__webhook = await channel.create_webhook(
                name=self._bot.user.display_name,
                avatar=self._bot.user.display_avatar,
            )
        return self.__webhook

    async def send(self, message: str):
        if self.__webhook is None:
            raise ClientException("Try to run Log.sync(log_channel_id) first")
        await self.__webhook.send(embed=Embed(
            color=Color.brand_red(),
            description=message[:2000]
        ))


class BotLogger(logging.Logger,):
    @staticmethod
    def _debug_(*msgs):
        return f'{Fore.CYAN}{" ".join(msgs)}{Style.RESET_ALL}'

    @staticmethod
    def _info_(*msgs):
        return f'{Fore.LIGHTMAGENTA_EX}{" ".join(msgs)}{Style.RESET_ALL}'

    @staticmethod
    def _error_(*msgs):
        return f'{Fore.RED}{" ".join(msgs)}{Style.RESET_ALL}'

    def debug(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.DEBUG):
            self._log(logging.DEBUG, self._debug_(msg), args, **kwargs)

    def info(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.INFO):
            self._log(logging.INFO, self._info_(msg), args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.WARNING):
            self._log(logging.WARNING, self._error_(msg), args, **kwargs)

    def error(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.ERROR):
            self._log(logging.ERROR, self._error_(msg), args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.CRITICAL):
            self._log(logging.CRITICAL, self._error_(msg), args, **kwargs)

    def line(self, level="info"):
        if level == "info":
            level = logging.INFO
        elif level == "debug":
            level = logging.DEBUG
        else:
            level = logging.INFO
        if self.isEnabledFor(level):
            self._log(
                level=logging.INFO,
                msg=Fore.BLACK + Style.BRIGHT + "-------------------------" + Style.RESET_ALL,
                args=()
            )


logging.setLoggerClass(BotLogger)
log_level = logging.INFO
loggers = set()

ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(log_level)
formatter = logging.Formatter(
    "%(asctime)s %(name)s[%(lineno)d] - %(levelname)s: %(message)s", datefmt="%m/%d/%y %H:%M:%S"
)
ch.setFormatter(formatter)


def get_logger(name=None) -> BotLogger:
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.addHandler(ch)
    loggers.add(logger)
    return logger  # type: ignore
