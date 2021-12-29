from textwrap import dedent

from nextcord.ext.commands import (
    CommandOnCooldown, MissingPermissions, NSFWChannelRequired,
    UserInputError, CommandNotFound, BotMissingPermissions, BadArgument,
    MissingRequiredArgument,
    Context, Cog, MemberNotFound
)
from nextcord import Member

from core.bot import MainBot
from core.constants import GangRole
from core.error import GangError
from utils.checks import is_staff
from utils.modules import dump_cache
from utils.util import Raise


class Events(Cog):
    def __init__(self, bot: MainBot):
        self._bot = bot

    @Cog.listener()
    async def on_command(self, ctx):
        pass

    @Cog.listener()
    async def on_member_remove(self, member: Member):
        await self._bot.weekly.delete(member.id)
        profile = self._bot.get_profile(member.id)
        if profile is None:
            return
        if profile.role is GangRole.L:
            await profile.gang.delete()
        await profile.delete()

    @Cog.listener()
    async def on_command_error(self, ctx: Context, error):
        if isinstance(error, BotMissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            await Raise(ctx, f"I am missing: `{missing_perms}` to run this command").info()
        if isinstance(error, CommandNotFound):  # Ignore these errors
            return
        elif isinstance(error, (UserInputError, BadArgument, MissingRequiredArgument, GangError, MemberNotFound)):
            await Raise(ctx, str(error)).info()
        elif isinstance(error, NSFWChannelRequired):
            await ctx.reply("This is not a NSFW channel!")
        elif isinstance(error, MissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            await Raise(ctx, f"You are missing: `{missing_perms}` to run this command").info()
        elif isinstance(error, CommandOnCooldown):
            # If the command is currently on cooldown trip this
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)
            if int(h) == 0 and int(m) == 0:
                await Raise(ctx, f"You must wait `{s:.2f}` seconds to use this command!").info()
            elif int(h) == 0 and int(m) != 0:
                await Raise(ctx, dedent(f"You must wait `{int(m)}` minutes\
                 and `{int(s)}` seconds to use this command!")).info()
            else:
                await Raise(ctx, dedent(f"You must wait `{int(h)}` hours,\
                 `{int(m)}` minutes and `{int(s)}` seconds to use this command!")).info()

        # Implement further custom checks for errors here...
        try:
            await self._bot.send_webhook_log(f"{ctx.channel.mention} {ctx.author} \n {error}")
        except TypeError:
            pass
        raise error

    @Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        await self._bot.send_webhook_log(f"event: {event} \n error: \n{args} \n{kwargs}")

    @Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # Whenever the bot is tagged, respond with its prefix
        if message.content.startswith(f"<@!{self._bot.user.id}>"):
            await message.channel.send(f":eyes: My prefix here is `!`", delete_after=10)

        # update msg cache
        if await is_staff(message):
            self._bot.loop.run_in_executor(None, dump_cache, self._bot, message, True)
        else:
            self._bot.loop.run_in_executor(None, dump_cache, self._bot, message)


def setup(bot):
    bot.add_cog(Events(bot))
