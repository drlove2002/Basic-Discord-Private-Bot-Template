from typing import TYPE_CHECKING
from json import JSONDecodeError
from typing import Union, Optional
from asyncio import TimeoutError

from nextcord import Embed, Message, Interaction, Colour, Color
from nextcord.ext.commands import Context
from core.constants import COMMAND_CHANNELS

if TYPE_CHECKING:
    from core.bot import MainBot


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
        *,
        title=Embed.Empty,
        description=Embed.Empty,
        timeout=100,
        delete_origin=False
):
    """
    This function sends an embed containing the params and then waits for a message to return
    Params:
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
    embed = Embed(title=title, description=description, color=Color.dark_theme())
    origin = await ctx.send(embed=embed)
    try:
        msg = await ctx.bot.wait_for(
            "message", timeout=timeout,
            check=lambda message: message.author == ctx.author and message.channel == ctx.channel,
        )
        if delete_origin:
            await origin.delete()
        if msg:
            return msg.content
    except TimeoutError:
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


async def get_advice(bot: "MainBot") -> str:
    try:
        json_data = await bot.session.get("https://api.adviceslip.com/advice").json()
    except JSONDecodeError:
        return ''
    text = json_data["slip"]["advice"]
    return text
