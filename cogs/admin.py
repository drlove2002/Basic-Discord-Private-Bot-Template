import platform

from nextcord import Embed, __version__ as dpy_v
from nextcord.ext.commands import (
    Cog, command, cooldown,
    BucketType
)

from core.bot import MainBot
from utils.checks import is_admin
from utils import logging

logger = logging.get_logger(__name__)


class Admin(Cog):
    def __init__(self, bot: MainBot):
        self.bot = bot

    async def cog_check(self, ctx) -> bool:
        return await is_admin(ctx)

    @command(
        name="stats", description="A useful command that displays bot statistics."
    )
    @cooldown(1, 3, BucketType.user)
    async def stats(self, ctx):
        """
        A useful command that displays bot statistics.
        """
        r = await self.bot.session.get(
            'https://source.unsplash.com/random/?server,computer,internet')
        embed = Embed(
            title=f'{self.bot.user.name} Stats',
            description='\uFEFF',
            colour=ctx.author.color,
            timestamp=ctx.message.created_at
        )

        embed.add_field(name='Bot Version:', value=self.bot.version)
        embed.add_field(name='Python Version:', value=platform.python_version())
        embed.add_field(name='nextcord.Py Version', value=dpy_v)
        embed.add_field(name='Total Guilds:', value=str(len(self.bot.guilds)))
        embed.add_field(name='Total Users:', value=str(len(set(self.bot.get_all_members()))))
        embed.add_field(name='Bot Developers:', value=f"{self.bot.owner}")
        embed.set_image(url=r.url)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)

        await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(Admin(bot))
