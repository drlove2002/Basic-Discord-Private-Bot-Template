from nextcord import DiscordException
from nextcord.ext.commands import Cog, BucketType, command, cooldown
from nextcord.ext import tasks
from core.bot import MainBot


class Mics(Cog):
    def __init__(self, bot: MainBot):
        self.bot = bot
        self.update.start()

    def cog_unload(self):
        self.update.cancel()

    @tasks.loop(minutes=5)
    async def update(self):
        if self.bot.test:
            return
        pass

    @update.before_loop
    async def before_message_update(self):
        await self.bot.wait_until_ready()

    @command()
    @cooldown(1, 3, BucketType.guild)
    async def ping(self, ctx):
        """
        Ping me to see how fast I can response!
        """
        await ctx.reply(f"> Pong! `{round(self.bot.latency * 1000)}ms`")
        try:
            await ctx.message.delete()
        except DiscordException:
            pass


def setup(bot: MainBot):
    bot.add_cog(Mics(bot))
