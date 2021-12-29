from typing import Union, List, Optional, TYPE_CHECKING

from nextcord import ui, PartialEmoji, Emoji, Message, Interaction, ButtonStyle
from nextcord.ext.commands import Context

from .constants import EMOJI
from utils.util import Raise

if TYPE_CHECKING:
    from .bot import MainBot


class SingleLink(ui.View):
    def __init__(self, url: str, label: str = None, emoji: Union[str, PartialEmoji, Emoji] = None):
        super().__init__()
        self.add_item(ui.Button(label=label, url=url, emoji=emoji))


# noinspection PyUnusedLocal
class YesNo(ui.View):
    children: List[ui.Button]

    def __init__(self, ctx: Optional[Context] = None):
        super().__init__(timeout=30)
        self.msg: Optional[Message] = None
        self.ctx = ctx
        self.value = None

    async def interaction_check(self, i: Interaction) -> bool:
        if self.ctx is None:
            return True
        if i.guild is None or\
                (i.channel_id == self.ctx.channel.id and self.ctx.author.id == i.user.id):
            return True
        await Raise(i, "You can't use this button").error()
        return False

    async def on_timeout(self) -> None:
        for child in self.children:
            if not child.disabled:
                child.disabled = True
        await self.msg.edit(view=self)

    @ui.button(style=ButtonStyle.green, emoji=EMOJI.TICK, label='\u200b')
    async def yes_button(self, button: ui.Button, inter: Interaction):
        await inter.response.defer()
        self.value = True
        self.stop()

    @ui.button(style=ButtonStyle.red, emoji=EMOJI.CROSS, label='\u200b')
    async def cancel_button(self, button: ui.Button, inter: Interaction):
        await Raise(inter, "Interaction cancelled, Let's pretend nothing happened 🙄", edit=True).info()
        self.value = False
        self.stop()


def add_views(bot: 'MainBot'):
    pass
