from asyncio import TimeoutError
import re
from datetime import datetime
from json import JSONDecodeError
from random import randint, choices
from textwrap import dedent
from typing import Optional, TYPE_CHECKING
from urllib.parse import quote

from pymongo import UpdateOne, DeleteOne
from dateutil.relativedelta import relativedelta
from nextcord import Member, Embed, Message, HTTPException, Color
from nextcord.ext.commands import converter
from nextcord.utils import utcnow
from aiolimiter import AsyncLimiter

from core import http
from core.views import SingleLink, WelcomeView, YesNo, Gift
from core.constants import AI_TOKEN, DEV_CHANNEL, LOUNGE1, EMOJI, booster_colors
from .util import human_readable_time, clean, get_advice
from . import logging
from .json import read_json

if TYPE_CHECKING:
    from core.bot import AiBot

buckets = {"ai_reply": AsyncLimiter(1, 0.3)}

logger = logging.get_logger(__name__)


async def welcome(bot, member: Member, *, test: bool = False):
    channel = member.guild.get_channel(874644809338458143 if test else 805206377302982707)
    view = WelcomeView(bot, member)
    view.msg = await channel.send(
        f"<a:Joined:925327087336824942>{member.mention}, "
        "***Welcome to Worldwide Community*** <a:earthblurple:876357028845596693>",
        embed=Embed(
            colour=member.accent_colour or randint(0, 0xFFFFFF),
            description=dedent(f"""\
            `-` <a:pinkverified:863685577047408660>**Assign your roles in** <#805206364594503720>\n
            `-` <a:purple_flame:839630427748696094>**Introduce yourself in** <#808341132609191947>\n
            `-` <a:Giveaways:827510244019666954>**Check giveaways in** <#805206357644935258>\n
            <a:heart:872377388229603390> Have a great day! You are our **{member.guild.member_count}th member**"""))
        .set_thumbnail(url=member.display_avatar.url)
        .set_image(url="https://media.giphy.com/media/c73dqeVb4QtvsOb5uo/giphy.gif"),
        view=view)
    logger.info(f"I welcomed {member}")


async def boost(bot: 'AiBot', member: Member, *, test: bool = False):
    webhook = bot.test_webhook if test else bot.boost_webhook
    await webhook.send(member.mention, embed=Embed(
        colour=Color.from_hsv(h=0.8190, s=randint(20, 100)/100, v=randint(65, 100)/100),
        description=dedent(f"""\
        **`-` Check <#842547178279010314> For premium colors.\n
        `-` Try <#919253361616887839> / <#837271163813101608> Channels.\n
        `-` <a:nitrobooster:819880599434166312> Read <#863694346997202944> to learn more.**"""), timestamp=utcnow())
        .set_thumbnail(url=member.display_avatar.url)
        .set_footer(
            text="Enjoy your new perks!",
            icon_url="https://cdn.discordapp.com/emojis/819942306928656405.gif?size=56")
    )
    logger.info(f"{member} Boosted server!")


async def server_vote(member: Member, channel):
    guild = member.guild
    channel = guild.get_channel(channel)
    vote_link = "https://top.gg/servers/512369682636865556/vote"
    msg = dedent(f"""\
    `-` <a:Tada2:824719743910412319>**Now you received <@&813877301732835358> role!**\n
    `-` <a:pinkverified:863685577047408660>**Check <#805206357644935258> channels.**""")
    await channel.send(
        f"<a:sparkles2:831678838610198559>{member.mention} **Has Voted!<a:sparkles2:831678838610198559>**",
        embed=Embed(colour=member.colour, description=msg)
        .set_thumbnail(url="https://cdn.discordapp.com/emojis/831823367140409374.png")
        .set_author(name=member, icon_url=member.display_avatar.url),
        view=SingleLink(vote_link, "Vote Link", "🔰"),
        delete_after=None if channel.id == 874644809338458143 else 25
    )
    logger.info(f"{member} Voted")


async def confession(message, bot: 'AiBot'):
    message = message
    if message.guild:
        await message.delete()
    else:
        data = await bot.rate_limit.find(message.author.id, projection={"confession": 1, "_id": 0})
        if data and data.get("confession") and data.get("confession") >= datetime.utcnow():
            await message.add_reaction("⏲️")
            return await message.author.send(
                f"⏰ You need to wait for {human_readable_time(data['confession'] - datetime.utcnow())}")
        new_time = utcnow() + relativedelta(minutes=5)
        view = YesNo(message)
        view.msg = await message.author.send(embed=Embed(
            colour=randint(0, 0xFFFFFF),
            description=dedent(f"""\
            Your message will be send to <#824015033775423569> channel!
            **Press {EMOJI.TICK} to confirm**""")), view=view)
        await view.wait()
        if view.value is None or not view.value:
            return
        await bot.rate_limit.upsert(message.author.id, {"confession": new_time, "ExpireAt": new_time})
        await message.add_reaction("<a:pinkverified:863685577047408660>")
        await message.author.send(embed=Embed(
            colour=randint(0, 0xFFFFFF),
            description="<a:pinkverified:863685577047408660>***Your message has been sent in*** <#824015033775423569>"))
    conf_channel = bot.get_channel(824015033775423569)
    log_channel = bot.get_channel(824015034829111316)
    em = Embed(
        colour=randint(0, 0xFFFFFF),
        title="<a:freakeyes:816687291963015188> __Confession__",
        description=re.sub(r'\d{18}(?!>)', lambda x: f"<@!{x.group()}>", message.content) or "[EMPTY]"
    ).set_footer(
        text="👀 Worldwide Anonymous Confession"
    ).set_thumbnail(url="https://i.ibb.co/b7BWJWH/Confession.png")
    msg = await conf_channel.send(embed=em)
    await msg.add_reaction("⭐")
    em.set_thumbnail(url=message.author.display_avatar.url)
    em.set_author(name=f"{message.author}", icon_url=message.author.display_avatar.url)
    em.set_footer(text=f"id: {message.author.id}")
    em.description += f"\n\n👀 `Confessed By:` {message.author.mention}"
    em.description += f"\n\n💭 `From:` {message.channel.mention if message.guild else 'DM'}"
    em.timestamp = message.created_at
    await log_channel.send(embed=em)


async def intros(message: Message, bot: 'AiBot'):
    counter = 0
    async for m in message.channel.history(limit=10):
        counter += 1
        if m.author == bot.user and counter > 3:
            await m.delete()
            description = dedent("""\
            - What would you like to be called?\n
            - How old are you?\n
            - Where do you live?\n
            - What's your first language?\n
            - What are your hobbies/what do you like?\n
            - What do you dislike?""")
            await message.channel.send(embed=Embed(
                colour=randint(0, 0xFFFFFF),
                title="Please use this template to introduce yourself:",
                description=f"```md\n{description}\n```",
            ).set_author(
                name="Welcome to the introduction channel!",
                icon_url="https://cdn.discordapp.com/emojis/811665342023073882.gif?v=1"
            ).set_footer(
                text=bot.guild.name, icon_url=message.guild.icon.replace(format="png").url
            ).set_thumbnail(url="https://i.ibb.co/b3kZF7H/Intros.png"))


async def bump_reminder(bot: 'AiBot', test: bool = False):
    if test:
        channel_id = DEV_CHANNEL
    else:
        channel_id = LOUNGE1
        bot.cache["guild_config"]["bump_time"] = datetime.utcnow() + relativedelta(minutes=30)
        await bot.config.upsert(bot.guild.id, {"bump_time": bot.cache["guild_config"]["bump_time"]})

    description = dedent("""\
    **__<a:animated_bell:827529460579303464>Time to bump the server<a:animated_bell:827529460579303464>__**
    > ***Please type `!d bump` in <#805206389889826866>***""")
    em = Embed(
        title="Disboard is off cooldown!",
        color=0x42f5f5,
        url="https://disboard.org/server/512369682636865556",
        description=description,
    )
    em.set_image(url="https://disboard.org/images/bot-command-image-bump.png")

    channel = bot.get_channel(channel_id)
    await channel.send(embed=em, delete_after=60)
    if not test:
        logger.info("Bump msg sent!")
        await bot.send_webhook_log(f"Bump reminder message sent <t:{int(utcnow().timestamp())}:F>")


async def bump_server(bot: 'AiBot', message: Message):
    def check(m):
        return m.author.id == 302050872383242240 \
               and m.channel == message.channel \
               and "Bump done" in m.embeds[0].description
    try:
        msg: Message = await bot.wait_for('message', check=check, timeout=10)
        if msg:
            bot.cache["guild_config"]["bump_time"] = datetime.utcnow() + relativedelta(hours=2)
            await bot.config.upsert(bot.guild.id, {"bump_time": bot.cache["guild_config"]["bump_time"]})
            await message.add_reaction("<a:Up2:829998593150681169>")
            await message.channel.send(
                embed=Embed(
                    color=randint(0, 0xFFFFFF),
                    description=dedent(f"""\
                    **__Next Bump Timer__**
                    {EMOJI.BELL} <t:{int(bot.cache['guild_config']['bump_time'].timestamp())}:R>""")
                ))
            match = re.findall(r'([0-9]{15,20})$', msg.embeds[0].description)
            logger.info(match)
            bumper = await converter.MemberConverter().query_member_by_id(bot, bot.guild, int(match[0]))
            if bumper is not None:
                await message.channel.send(
                    bumper.mention,
                    embed=Embed(
                        color=bumper.color,
                        description=f"<a:catjam:839291892579303434>**Thanks for bumping!**"
                    ),
                    delete_after=10
                )
            logger.info(f'Server bumped! at {datetime.utcnow()} by {bumper}')
    except TimeoutError:
        pass


async def sent_auto_msg(bot: 'AiBot', *, test: bool = False, msg_index: Optional[int] = None):
    message_index = "msg_index_test" if test else "msg_index"
    msg_list = read_json("auto_messages")
    msg = msg_list[msg_index if msg_index is not None and test else bot.cache["guild_config"][message_index]]
    if test:
        webhook = bot.test_webhook
    else:
        webhook = bot.lounge_webhook
        bot.cache["guild_config"]["send_message_time"] = datetime.utcnow() + relativedelta(
            hours=1, minutes=randint(1, 60))
        await bot.config.upsert(bot.guild.id, {"send_message_time": bot.cache["guild_config"]["send_message_time"]})

    if bot.cache["guild_config"][message_index] >= len(msg_list) - 1:
        bot.cache["guild_config"][message_index] = 0
    else:
        bot.cache["guild_config"][message_index] += 1
    await bot.config.upsert(bot.guild.id, {message_index: bot.cache["guild_config"][message_index]})
    if msg.get("title") == "__Worldwide__":
        if choices([True, False], weights=[7, 3])[0]:
            advice = await get_advice()
            if advice:
                msg["description"] = f"{EMOJI.SPARKLE3}***{advice[:-1]}***{EMOJI.SPARKLE3}"
    em = Embed(
        colour=randint(0, 0xFFFFFF),
        title=msg.get("title"),
        description=msg.get("description")
    )
    em.set_thumbnail(url=msg.get("thumbnail"))
    await webhook.send(
        content=msg.get("content"),
        embed=em,
        avatar_url=bot.user.display_avatar.url,
        username=bot.user.display_name,
    )
    if not test:
        logger.info(f"Msg sent via webhook!")
        await bot.send_webhook_log(f"Bump reminder message sent <t:{int(utcnow().timestamp())}:F>")


async def ai_reply(bot: 'AiBot', message: Message):
    async with buckets.get("ai_reply"):
        if message.channel.id not in [805206377302982707, 824015030713974794]:
            msg = clean(message.content)
            if msg:
                if message.content.startswith("ww"):
                    msg = quote(msg[2:])
                elif message.content.startswith(f"<@!{bot.user.id}>"):
                    msg = quote(msg[18:])
                else:
                    msg = quote(msg)
                url = f"https://api.monkedev.com/fun/chat?msg={msg}&uid={message.author.id}&key={AI_TOKEN}"
                try:
                    r = await http.get(url, res_method="json", no_cache=True)
                except (JSONDecodeError, HTTPException):
                    r = []
                    pass
                if r.get('response') is not None:
                    await message.author.trigger_typing()
                    await message.reply(content=r.get('response'), mention_author=False)


async def remove_color(member: Member):
    roles = member.roles[1:]  # remove @everyone
    for role in reversed(roles):
        if role.colour.value:
            if role.id in booster_colors:
                await member.remove_roles(role)
                logger.info(f"{role.name} removed from {member.display_name}")
                return


async def drop_gift(bot: 'AiBot', test: bool = False):
    channel = bot.guild.get_channel(DEV_CHANNEL if test else LOUNGE1)
    if not test:
        messages = await channel.history(limit=5).flatten()
        if messages[0].created_at.minute == messages[4].created_at.minute:
            bot.cache["guild_config"]["dropGift"] = datetime.utcnow() + relativedelta(hours=1, minutes=randint(1, 60))
            await bot.config.upsert(bot.guild.id, {"dropGift": bot.cache["guild_config"]["dropGift"]})
        else:
            return
    view = Gift(bot)
    view.msg = await channel.send(
        embed=Embed(
            title=f"{EMOJI.SPARKLE}__Surprise Gift__{EMOJI.SPARKLE}",
            color=randint(0, 0xFFFFFF),
            description=dedent(f"**Press `🎁` to claim the gift.. hurry up!**\n")
        ).set_image(
            url="https://c.tenor.com/U9d3CCCOVoAAAAAC/gift-gifts.gif"
        ).set_thumbnail(url="https://cdn.discordapp.com/emojis/817399261087924254.gif"),
        view=view)
    await bot.send_webhook_log(f"🎁 Gift appeared in lounge at <t:{int(datetime.utcnow().timestamp())}:F>")
    logger.info(f'🎁 Gift appeared in lounge')


async def weekly_tax(bot: 'AiBot'):
    bot.cache["guild_config"]["weekly"] = datetime.utcnow() + relativedelta(days=7)
    await bot.config.upsert(bot.guild.id, {"weekly": bot.cache["guild_config"]["weekly"]})
    all_user = await bot.cookies.get_all()
    payload = []
    for user in all_user:
        if user["balance"] <= 1:
            payload.append(DeleteOne({"_id": user["_id"]}))
        else:
            payload.append(UpdateOne({"_id": user["_id"]}, {"$set": {"balance": int(user["balance"]/2)}}))
    if payload:
        await bot.cookies.bulk_write(payload)
    await bot.fun_webhook.send(embed=Embed(
        colour=0xe6cea0,
        timestamp=utcnow(),
        title=f"{EMOJI.alert} __Weekly Cookies Tax Applied__",
        description=dedent(f"""\
            {EMOJI.BELL}Member's cookies amount is being half of what they had\n
            **{EMOJI.TICK}This tax is applied to every member**\n
            **🗜️Tax: `50%`**
            """)
    ).set_thumbnail(
        url="https://c.tenor.com/lHLiPQ3lllkAAAAd/tax-return-tax-refund.gif"
    ), username=bot.user.display_name, avatar_url=bot.user.display_avatar)


async def role_expiry(bot: 'AiBot'):
    payload = []
    for user in bot.cache["rr"].keys():
        print(bot.cache["rr"])
        for role, _t in bot.cache["rr"][user].items():
            if role == "_id":
                continue
            if _t <= datetime.utcnow():
                await bot.guild.get_member(int(user)).remove_roles(role, reason="Rent period expired")
                payload.append(UpdateOne({"_id": user}, {"$unset": {role: _t}}, upsert=True))
    if payload:
        await bot.rent_role.bulk_write(payload)
