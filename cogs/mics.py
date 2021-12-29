from datetime import datetime, timedelta

from nextcord import DiscordException
from nextcord.ext.commands import Cog, BucketType, command, cooldown
from nextcord.ext import tasks
from core.bot import MainBot
from core.leaderboad import Leaderboard
from utils.modules import staff_activity, vote_check


class Mics(Cog):
    def __init__(self, bot: MainBot):
        self.bot = bot
        self.message_update.start()

    def cog_unload(self):
        self.message_update.cancel()

    @tasks.loop(minutes=5)
    async def message_update(self):
        if self.bot.test:
            return
        lb = Leaderboard(self.bot)
        w_dt: timedelta = self.bot.cache["g_config"]["weekly_time"] - datetime.utcnow()
        if w_dt <= timedelta(0):
            return await lb.reset_msg_lbs()
        d_dt: timedelta = self.bot.cache["g_config"]["daily_time"] - datetime.utcnow()
        if d_dt <= timedelta(0):
            await staff_activity(self.bot)
            self.bot.loop.create_task(lb.reset_daily_lb())
            self.bot.loop.create_task(vote_check(self.bot))
        self.bot.loop.create_task(lb.update_msg_lbs(w_dt, d_dt))

    @message_update.before_loop
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
