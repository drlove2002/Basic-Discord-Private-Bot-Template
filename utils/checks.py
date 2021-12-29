"""The permission system of the bot is based on a "just works" basis
You have permissions and the bot has permissions. If you meet the permissions
required to execute the command (and the bot does as well) then it goes through
and you can execute the command.
Certain permissions signify if the person is a moderator (Manage Server) or an
admin (Administrator). Having these signify certain bypasses.
Of course, the owner will always be able to execute commands."""
from typing import Union, Optional, List

from nextcord import DMChannel, DiscordException, Message, TextChannel, Member
from nextcord.ext.commands import Context, check

from core.constants import COMMAND_CHANNELS, ROLE
from .util import Raise


async def check_permissions(ctx: Context, perms, *, checks=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    resolved = ctx.channel.permissions_for(ctx.author)
    return checks(getattr(resolved, name, None) == value for name, value in perms.items())


def has_permissions(*, checks=all, **perms):
    async def pred(ctx):
        return await check_permissions(ctx, perms, checks=checks)

    return check(pred)


def is_invoked_with_command(ctx: Union[Context, Message]):
    if isinstance(ctx, Message):
        return False
    return ctx.valid and ctx.invoked_with in (*ctx.command.aliases, ctx.command.name)


async def check_guild_permissions(ctx, perms, *, checks=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if ctx.guild is None:
        return False

    resolved = ctx.author.guild_permissions
    return checks(getattr(resolved, name, None) == value for name, value in perms.items())


def has_guild_permissions(*, checks=all, **perms):
    async def pred(ctx):
        return await check_guild_permissions(ctx, perms, checks=checks)

    return check(pred)


# These do not take channel overrides into account

def can_bot(perm: str, ctx: Context, channel: Optional[TextChannel] = None) -> bool:
    channel = channel or ctx.channel
    return (
            isinstance(channel, DMChannel)
            or getattr(channel.permissions_for(ctx.guild.me), perm)
    )


def can_send(ctx: Context, channel: Optional[TextChannel] = None) -> bool:
    return can_bot("send_messages", ctx, channel)


def can_embed(ctx: Context, channel: Optional[TextChannel] = None) -> bool:
    return can_bot("embed_links", ctx, channel)


def can_upload(ctx: Context, channel: Optional[TextChannel] = None) -> bool:
    return can_bot("attach_files", ctx, channel)


def can_react(ctx: Context, channel: Optional[TextChannel] = None) -> bool:
    return can_bot("add_reactions", ctx, channel)


# noinspection PyProtectedMember
async def staff_perms(ctx: Context, allowed_list: List[int]) -> bool:
    if not set(allowed_list).isdisjoint(ctx.author._roles):
        return True
    if is_invoked_with_command(ctx):
        await Raise(
            ctx,
            f"Only <@&{allowed_list[0]}> and higher staffs can use this command",
            delete_after=None if ctx.channel.id in COMMAND_CHANNELS else 5
        ).info()
        try:
            await ctx.message.delete()
        except DiscordException:
            pass
    return False


# noinspection PyProtectedMember
def is_donor(member: Member) -> bool:
    donor_roles = [805206231278419980, 823187151717138442, 823187155991134258, 805206230721232926]
    return any(_id in member._roles for _id in donor_roles)


async def is_staff(ctx: Context) -> bool:
    return await staff_perms(ctx, [ROLE.STAFF, ROLE.MOD, ROLE.SR_MOD, ROLE.ADMIN, ROLE.MANAGER, ROLE.OWNER])


async def is_mod(ctx: Context) -> bool:
    return await staff_perms(ctx, [ROLE.MOD, ROLE.SR_MOD, ROLE.ADMIN, ROLE.MANAGER, ROLE.OWNER])


async def is_sr_mod(ctx: Context) -> bool:
    return await staff_perms(ctx, [ROLE.SR_MOD, ROLE.ADMIN, ROLE.MANAGER, ROLE.OWNER])


async def is_admin(ctx: Context) -> bool:
    return await staff_perms(ctx, [ROLE.ADMIN, ROLE.MANAGER, ROLE.OWNER])


async def is_manager(ctx: Context) -> bool:
    return await staff_perms(ctx, [ROLE.MANAGER, ROLE.OWNER])


async def in_command_channel(ctx: Context):
    if ctx.channel.id in COMMAND_CHANNELS:
        return True
    if is_invoked_with_command(ctx):
        await Raise(ctx, "Only usable in commands channel", delete_after=5).info()
        try:
            await ctx.message.delete()
        except DiscordException:
            pass
    return False


def mod_or_permissions(**perms):
    perms['manage_guild'] = True

    async def predicate(ctx):
        return await check_guild_permissions(ctx, perms, checks=any)

    return check(predicate)


def admin_or_permissions(**perms):
    perms['administrator'] = True

    async def predicate(ctx):
        return await check_guild_permissions(ctx, perms, checks=any)

    return check(predicate)


def is_in_guilds(*guild_ids):
    def predicate(ctx):
        guild = ctx.guild
        if guild is None:
            return False
        return guild.id in guild_ids

    return check(predicate)


def in_dm(ctx: Context):
    return not ctx.guild


async def in_vc(ctx: Context):
    if ctx.author.voice is None and is_invoked_with_command(ctx):
        try:
            await ctx.message.delete()
        except DiscordException:
            pass
        await Raise(
            ctx,
            "Hay, you can't use this command unless you are in a voice channel",
            delete_after=None if ctx.channel.id in COMMAND_CHANNELS else 5
        ).info()
    return ctx.author.voice
