__version__ = '0.0.0'

# Standard libraries
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Third party libraries
import aiohttp
from nextcord import (
    __version__ as dpy_v,
    Status, Activity, ActivityType,
    Embed, Color, Member, Intents, Guild, Webhook
)
from nextcord.ext.commands import Bot, when_mentioned_or
import motor.motor_asyncio
from dotenv import load_dotenv

# Local code
from utils.keep_alive import webserver
from .constants import GUILD, CHANNEL
from utils.json import read_json, json_unset, write_json
from utils.mongo import Document
from utils import logging
# from .views import add_views

load_dotenv()
ROOT_DIR = str(Path(__file__).parents[1])
logger = logging.get_logger(__name__)
logger.info(f"{ROOT_DIR}\n-----")

__all__ = ["BaseMainBot", "MainBot"]


async def get_prefix(client, message):
    prefixes = ["!"]
    return when_mentioned_or(*prefixes)(client, message)


class BaseMainBot(Bot):
    def __init__(self):
        super().__init__(
            command_prefix=get_prefix,
            case_insensitive=True,
            owner_id=506498413857341440,
            intents=Intents.all(),
            strip_after_prefix=True,
            status=Status.online,
            activity=Activity(type=ActivityType.watching, name="Worldwide 👀")
        )
        # Defining a few things
        self.guild: Optional[Guild] = None
        self.test: bool = False  # True: will disable few events trigger, for easier testing
        # Webhook session
        self.session = aiohttp.ClientSession(trust_env=True)
        self.log_webhook = Webhook.from_url(os.getenv("logging"), session=self.session)

        self.__mongo = motor.motor_asyncio.AsyncIOMotorClient(str(os.getenv("mongo")))
        self._mongo_setup()
        self._init_json()

    def _mongo_setup(self):
        """MongoDB setup"""
        self.db = self.__mongo["database"]  # Type your database name here

        self.collection = Document(self.db, "collection")  # Type your collection name here
        logger.info("Initialized Database")

    def _init_json(self):
        """Initialize Cache"""
        self.cache: Dict[str, Dict[str, Any]] = {"config": read_json("config")}
        logger.info("Initialized Cache")

    def startup(self):
        self: MainBot
        logger.line()
        # add_views(self)
        # logger.info(f"View are added")
        logger.line()
        logger.info(f"Bot Version: {self.version}", )
        logger.info("Nextcord.py: v%s", dpy_v)
        logger.line()
        for file in os.listdir(ROOT_DIR + "/cogs"):
            if file.endswith(".py") and not file.startswith("_"):
                self.load_extension(f"cogs.{file[:-3]}")
                logger.info(f"{file[:-3]} Cog has been loaded")
                logger.line()

    async def on_ready(self):
        # On ready, print some details to standard out
        webserver()
        self.guild = self.get_guild(GUILD.MAIN)
        self.startup()

        if self.cache:
            if restart_msg := self.cache["config"].get('restart_msg', False):
                channel = self.guild.get_channel(CHANNEL.DEV)
                msg = await channel.fetch_message(restart_msg)
                await msg.edit(embed=Embed(
                    color=Color.brand_green(),
                    description="***<a:verify_white:859557747648364544>Restarted!***"
                ))
                json_unset(['restart_msg'], "config")
            for cache in ["staff_cache", "msg_cache"]:
                write_json({}, cache)
        logger.line()
        logger.info(f"Logged in as: {self.user.name} : {self.user.id}")

    @property
    def version(self):
        return __version__

    @property
    async def owner(self) -> Member:
        return self.guild.get_member(self.owner_id)

    @property
    def prefix(self) -> str:
        return "rr"

    async def get_prefix(self, message=None):
        prefixes = ["rr"]
        if self.test:
            prefixes.append("$")
        return when_mentioned_or(*prefixes)(self, message)

    @property
    def token(self) -> str:
        token = os.getenv("token")
        return token

    async def send_webhook_log(self, msg: str):
        await self.log_webhook.send(
            embed=Embed(color=Color.brand_red(), description=msg), username=self.user.display_name)


class MainBot(BaseMainBot):
    """
    Our subclass of discord.ext.commands.Bot
    Will be used only for typehints
    """
