from datetime import datetime

from dateutil.relativedelta import relativedelta
from typing import TYPE_CHECKING
import re
from json import JSONDecodeError
from random import randint
from typing import Union, Optional
from asyncio import TimeoutError

from pymongo import UpdateOne
from nextcord import Embed, Message, Interaction, Colour, Member, Emoji
from nextcord.ext.commands import Context, MemberConverter, TextChannelConverter, VoiceChannelConverter, ChannelNotFound

from urllib.request import urlopen

from core import http
from core.constants import COMMAND_CHANNELS

if TYPE_CHECKING:
    from core.bot import AiBot


NORMALIZE_CHARS = {'Š': 'S', 'š': 's', 'Ð': 'Dj', 'Ž': 'Z', 'ž': 'z', 'À': 'A', 'Á': 'A', 'Ã': 'A', 'Ä': 'A',
                   'Å': 'A', 'Æ': 'A', 'Ç': 'C', 'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E', 'Ì': 'I', 'Í': 'I',
                   'Ï': 'I', 'Ñ': 'N', 'Ń': 'N', 'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O', 'Ø': 'O',
                   'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U', 'Ý': 'Y', 'Þ': 'B', 'ß': 'Ss', 'à': 'a', 'á': 'a',
                   'ã': 'a', 'ä': 'a', 'å': 'a', 'æ': 'a', 'ç': 'c', 'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
                   'ì': 'i', 'í': 'i', 'ï': 'i', 'ð': 'o', 'ñ': 'n', 'ń': 'n', 'ò': 'o', 'ó': 'o', 'ô': 'o',
                   'õ': 'o', 'ö': 'o', 'ø': 'o', 'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u', 'ý': 'y', 'þ': 'b',
                   'ÿ': 'y', 'ƒ': 'f', 'ă': 'a', 'î': 'i', 'â': 'a', 'ș': 's', 'ț': 't', 'Ă': 'A', 'Î': 'I',
                   'Â': 'A', 'Ș': 'S', 'Ț': 'T', }
ALPHABETS = urlopen("https://raw.githubusercontent.com/JEF1056/clean-discord/master/src/alphabets.txt").read().decode(
    "utf-8").strip().split("\n")
for alphabet in ALPHABETS[1:]:
    alphabet = alphabet
    for ind, char in enumerate(alphabet):
        try:
            NORMALIZE_CHARS[char] = ALPHABETS[0][ind]
        except KeyError:
            print(alphabet, len(alphabet), len(ALPHABETS[0]))
            break

r2 = re.compile(r'[\U00003000\U0000205F\U0000202F\U0000200A\U00002000-\U00002009\U00001680\U000000A0\t]+')
r5 = re.compile(r'([.\'"@?!a-z])\1{4,}', re.IGNORECASE)
r6 = re.compile(r'\s(.+?)\1+\s', re.IGNORECASE)
r8 = re.compile(r'([\s!?@"\'])\1+')
r9 = re.compile(r'\s([?.!\"](?:\s|$))')


def clean(text: str) -> str:
    unique = [i for i in list(set(text)) if i not in ALPHABETS[0]]  # handle special chars from other langs
    for _char in unique:
        try:
            text = text.replace(_char, NORMALIZE_CHARS[_char])
        except KeyError:
            pass
    text = re.sub(r2, " ", text)  # handle... interesting spaces
    text = re.sub(r5, r"\1\1\1", text)  # handle excessive repeats of punctuation, limited to 3
    text = re.sub(r6, r" \1 ", text)  # handle repeated words
    text = re.sub(r8, r"\1", text)  # handle excessive spaces or excessive punctuation
    text = re.sub(r9, r'\1', text)  # handle spaces before punctuation but after text
    text = text.strip().replace("\n", "/n")  # handle newlines
    text = text.encode("ascii", "ignore").decode()  # remove all non-ascii
    text = text.strip()  # strip the line
    return text


class DotDict(dict):
    """dot.notation access to dictionary attributes"""

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError(k)


async def get_message(
        ctx: Context,
        title: Optional[str] = Embed.Empty,
        description: Optional[str] = "\uFEFF",
        *, _type: Optional[str] = "string",
        timeout: Optional[Union[int, float]] = 100
):
    """
    This function sends an embed containing the params and then waits for a message to return
    Params:
     - bot (commands.Bot object) :
     - ctx (context object) : Used for sending msgs n stuff
     - Optional Params:
        - title (string) : Embed title
        - description (string) : Embed description
        - timeout (int) : Timeout for wait_for
    Returns:
     - msg.content (string) : If a message is detected, the content will be returned
    or
     - False (bool) : If a timeout occurs
    """

    embed = Embed(color=randint(0, 0xFFFFFF), title=title, description=description)
    question = await ctx.send(embed=embed)
    try:
        msg = await ctx.bot.wait_for(
            "message",
            timeout=timeout,
            check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
        )
        if msg:
            await question.delete()
            if _type == "string":
                result = msg.content
            elif _type == "textchannel":
                try:
                    result = await TextChannelConverter().convert(ctx, msg.content)
                except ChannelNotFound:
                    return False
            elif _type == "voicechannel":
                try:
                    result = await VoiceChannelConverter().convert(ctx, msg.content)
                except ChannelNotFound:
                    return False
            elif _type == "member":
                try:
                    result = await MemberConverter().convert(ctx, msg.content)
                except ChannelNotFound:
                    return False
            else:
                result = msg.content
            return result
    except TimeoutError:
        await Raise(ctx, "Error happened!, RETRY!").error()
        return False


class Raise:
    INFO = DotDict({"emoji": "<a:alert:834006242522693644>", "color": Colour.yellow()})
    ERROR = DotDict({"emoji": "<a:crossmark:881496170122342470>", "color": Colour.red()})
    SUCCESS = DotDict({"emoji": "<a:Verified2:824719741984833587>", "color": Colour.green()})

    def __init__(
            self,
            ctx: Union[Context, Interaction],
            message: str, *,
            delete_after: Optional[Union[int, float]] = 10,
            edit: Optional[Union[Message, bool]] = False):
        self.ctx = ctx
        self.msg = message
        self.del_after = None if ctx.channel.id in COMMAND_CHANNELS else delete_after
        self.edit = edit

    async def __response(self, message: str, emoji_dict, delete_after, edit) -> Optional[Message]:
        if isinstance(self.ctx, Interaction):
            if edit:
                await self.ctx.response.edit_message(
                    embed=Embed(color=emoji_dict.color, description=f"{emoji_dict.emoji} **{message}**"), view=None)
            await self.ctx.response.send_message(
                embed=Embed(color=emoji_dict.color, description=f"{emoji_dict.emoji} **{message}**"), ephemeral=True)
        else:
            if edit:
                return await edit.send(
                    self.ctx.author.mention,
                    embed=Embed(color=emoji_dict.color, description=f"{emoji_dict.emoji} **{message}**"),
                    delete_after=delete_after
                )
            return await self.ctx.send(
                self.ctx.author.mention,
                embed=Embed(color=emoji_dict.color, description=f"{emoji_dict.emoji} **{message}**"),
                delete_after=delete_after
            )

    async def error(self) -> Optional[Message]:
        return await self.__response(self.msg, self.ERROR, self.del_after, self.edit)

    async def info(self) -> Optional[Message]:
        return await self.__response(self.msg, self.INFO, self.del_after, self.edit)

    async def success(self) -> Optional[Message]:
        return await self.__response(self.msg, self.SUCCESS, self.del_after, self.edit)


def human_readable_time(dt, short: bool = False):
    d = dt.days
    m, s = divmod(dt.seconds, 60)
    h, m = divmod(m, 60)
    if short:
        if int(d):
            return f"`{d}`d `{h}`h `{m}`m `{s}`s"
        elif int(h):
            return f"`{h}`h `{m}`m `{s}`s"
        elif int(m):
            return f"`{m}`m `{s}`s"
        else:
            return f"`{s}`s"
    else:
        if int(d):
            return f"`{d}` day(s) `{h}` hour(s) `{m}` minute(s) `{s}` seconds"
        elif int(h):
            return f"`{h}` hour(s) `{m}` minute(s) `{s}` seconds"
        elif int(m):
            return f"`{m}` minute(s) `{s}` seconds"
        else:
            return f"`{s}` seconds"


def clean_code(content):
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:])[:-3]
    return content


async def get_advice() -> str:
    try:
        json_data = await http.get(
            f"https://api.adviceslip.com/advice", res_method="json",
            no_cache=True)
    except JSONDecodeError:
        return ''
    text = json_data["slip"]["advice"]
    return text


def dump_cache(bot: 'AiBot', author_id, count=1):
    _id = str(author_id)
    bot.cache["msg_cache"][_id] = bot.cache["msg_cache"].get(_id, 0) + count


async def upload_cache(bot: 'AiBot'):
    cache_data = bot.cache.get("msg_cache")
    if cache_data is None:
        return
    requests = []
    for _id, count in cache_data.items():
        requests.append(UpdateOne({"_id": int(_id)}, {"$inc": {"balance": int(count/2)}}, upsert=True))
        requests.append(
            UpdateOne(
                {"_id": int(_id)}, {"$set": {"ExpireAt": datetime.utcnow() + relativedelta(days=7)}},
                upsert=True)
        )
    await bot.loop.create_task(bot.cookies.bulk_write(requests))
    bot.cache["msg_cache"].clear()


async def get_profile(bot: "AiBot", user_id, mode="balance"):
    profile = await bot.cookies.find(user_id)
    if not profile.get(mode):
        return None
    return profile[mode]


# noinspection PyProtectedMember
def gender_emoji(bot: 'AiBot', user: Member) -> Emoji:
    if 805206264765481041 in user._roles:
        return bot.get_emoji(909129442478149693)
    elif 805206265500401666 in user._roles:
        return bot.get_emoji(909129442700431370)
    else:
        return bot.get_emoji(909130065030316032)
