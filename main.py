import argparse
import functools
import os
import sys

from nextcord import DiscordException, Status, Activity, ActivityType, Embed, Color
from nextcord.ext.commands import check

from core.bot import BaseMainBot
from core.constants import EMOJI
from utils.checks import is_manager
from utils.json import json_upsert

parser = argparse.ArgumentParser()
parser.add_argument("id", nargs='?', default=None)
args = parser.parse_args()
bot = BaseMainBot()


@bot.command(aliases=["restart"], description="Restart the bot")
@check(is_manager)
async def _restart(ctx):
    try:
        await ctx.message.delete()
    except DiscordException:
        pass
    await bot.change_presence(
        status=Status.idle,
        activity=Activity(type=ActivityType.watching, name="and Restarting...⚠️")
    )
    msg = await ctx.send(embed=Embed(
        color=Color.brand_red(),
        description=f"***{EMOJI.loading}Restarting...***"
    ))
    json_upsert({"restart_msg": msg.id}, "config")
    bot.loop.run_in_executor(None, functools.partial(os.system, "python3 restart.py " + str(ctx.channel.id)))
    await bot.close()
    sys.exit(0)


if __name__ == "__main__":
    # When running this file, if it is the 'main' file
    # I.E its not being imported from another python file run this
    bot.run(bot.token)
