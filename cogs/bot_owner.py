import asyncio
import contextlib
import io
import os
import sys

from textwrap import indent, dedent
import traceback
from traceback import format_exception

from nextcord import Embed, Colour, DiscordException
from nextcord.ext.commands import (
    bot_has_permissions,
    Cog, command,
    cooldown,
    BucketType,
    is_owner, check, Context
)

from core.bot import MainBot
from core.constants import COMMAND_CHANNELS
from utils.checks import is_manager
from core.pawgenator import Paginator
from utils.util import clean_code


class BotOwner(Cog):
    def __init__(self, bot: MainBot):
        self.bot = bot

    @command()
    @is_owner()
    async def test(self, ctx: Context):
        pass

    @command(name="taskcount", aliases=["tc"])
    @check(is_manager)
    @cooldown(1, 3, BucketType.user)
    async def task_count(self, ctx: Context):
        """
        Return total task count running in background in the bot.
        Use for tracking the load on the bot
        """
        tasks = asyncio.Task.all_tasks()
        filtered_task = [task for task in tasks if not task.done()]
        await ctx.reply(
            embed=Embed(
                color=Colour.random(),
                title="__Background Tasks__",
                description=dedent(f"""\
                > **Total tasks ever created: `{len(tasks)}`**

                > **Currently tasks running in background: `{len(filtered_task)}`**
                """)).set_thumbnail(url=self.bot.get_emoji(809890706784649237).url),
            delete_after=None if ctx.channel.id in COMMAND_CHANNELS else 10
        )

    @command()
    @is_owner()
    async def getcache(self, ctx: Context):
        cache = self.bot.cache["msg_cache"]
        description = str(cache.items())
        pages = [description[i: i + 2000] for i in range(0, len(description), 2000)]
        em = []
        for index, page in enumerate(pages):
            em.append(Embed(
                color=Colour.random(),
                title="Cache Details",
                description=f"```py\n{page}\n```"
            ).set_footer(text=f"Page {index}/{len(pages)}"))
        if len(em) == 1:
            await ctx.reply(embed=em)
        else:
            await Paginator(channel=ctx.channel, user=ctx.author, embeds=em).start()

    @command(
        name="logout",
        aliases=["disconnect", "close", "stopbot"],
        description="If the user running the command owns the bot then this will disconnect the bot from"
    )
    @is_owner()
    async def logout(self, ctx):
        await ctx.reply(f"Hey {ctx.author.mention}, I am now logging out :wave:")
        sys.exit()

    @command(description="Bot will leave the server", hidden=True)
    @is_owner()
    async def leave(self, ctx, guild: int = None):
        if not guild:
            return await ctx.reply("Please enter the guild id")
        guild = self.bot.get_guild(guild)
        if not guild:
            return await ctx.reply("I don't recognize that guild.")
        await guild.leave()
        await ctx.author.send(f":ok_hand: Left guild: {guild.name} ({guild.id})")

    @command(
        name='reload', description="Reload all/one of the bots cogs!"
    )
    @check(is_manager)
    async def reload(self, ctx, *files: str):
        msg = "**Reloading Modules..**"
        for module in files:
            ext = f"{module.split('.')[-1].lower()}.py"
            if not os.path.exists(f"./{'/'.join(module.split('.')[:-1])}/{ext}"):
                # if the file does not exist
                msg += f"```diff\n-Failed to reload: `{ext}`\nThis cog does not exist.\n```"
            elif ext.endswith(".py") and not ext.startswith("_"):
                try:
                    async with ctx.typing():
                        self.bot.unload_extension(module)
                        self.bot.load_extension(module)
                    msg += f"```json\nSuccessfully loaded extension {files}\n```"
                except DiscordException:
                    desired_trace = traceback.format_exc()
                    msg += f"```diff\n-Failed to reload: `{ext}`\n{desired_trace}\n```"
            await ctx.reply(embed=Embed(description=msg))

    @command(name="eval", aliases=["exec", "evl"], hidden=True)
    @bot_has_permissions(embed_links=True)
    @check(is_manager)
    async def eval(self, ctx, *, code):
        code = clean_code(code)
        local_variables = {
            "Embed": Embed,
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message
        }
        stdout = io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout):
                exec(f"async def func():\n{indent(code, '    ')}", local_variables)
                obj = await local_variables["func"]()
                result = f"{stdout.getvalue()}\n-- {obj}\n"
        except Exception as e:
            result = "".join(format_exception(e, e, e.__traceback__))
        pages = [result[i: i + 2000] for i in range(0, len(result), 2000)]
        em = []
        for index, page in enumerate(pages):
            em.append(Embed(
                color=Colour.random(),
                description=f"```py\n{page}\n```"
            ).set_footer(text=f"Page {index}/{len(pages)}"))
        await Paginator(channel=ctx.channel, user=ctx.author, embeds=em).start()


def setup(bot):
    bot.add_cog(BotOwner(bot))
