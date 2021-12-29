from typing import List, Optional
from nextcord import (
    ButtonStyle, SelectOption, Interaction, ui,
    Embed, Message, TextChannel, Member
)
from utils.util import Raise

__all__ = ["Paginator"]


class Paginator:
    __slots__ = ("channel", "user", "embeds", "view")

    def __init__(
        self,
        channel: TextChannel,
        user: Member,
        embeds: List[Embed]
    ):
        self.channel = channel
        self.user = user
        self.embeds = embeds
        self.view = PaginatorView(self.channel, self.user, self.embeds)

    async def start(self):
        self.view.msg = await self.channel.send(embed=self.embeds[0], view=self.view)

    async def add_dropdown(self, mapping: List[List[SelectOption]], help_command):
        self.view.add_item(SelectCommand(mapping, help_command))


class PaginatorView(ui.View):
    def __init__(
        self,
        channel: TextChannel,
        user: Member,
        embeds: List[Embed]
    ):
        super().__init__(timeout=30)
        self.channel = channel
        self.user = user
        self.embeds = embeds
        self.index = 0
        self.msg: Optional[Message] = None
        self.add_item(
            ui.Button(custom_id="page_count", label=f"Page {self.index + 1}/{len(self.embeds)}", disabled=True))

    async def interaction_check(self, interaction) -> bool:
        if interaction.channel_id == self.channel.id and self.user.id == interaction.user.id:
            return True
        await Raise(interaction, "You can't use this button").error()
        return False

    async def button_callback(self, inter: Interaction):
        for item in self.children:
            if isinstance(item, ui.Button) and item.custom_id == "page_count":
                item.label = f"Page {self.index + 1}/{len(self.embeds)}"
            if isinstance(item, SelectCommand) and item.custom_id == "command_paginator_dropdown":
                item.update_options(self.index)

        await inter.response.edit_message(
            embed=self.embeds[self.index], view=self)

    @ui.button(emoji="⬅️", style=ButtonStyle.gray)
    async def button_left_callback(self, button: ui.Button, inter: Interaction):
        if self.index == 0:
            self.index = len(self.embeds) - 1
        else:
            self.index -= 1

        await self.button_callback(inter)

    @ui.button(emoji="➡️", style=ButtonStyle.gray)
    async def button_right_callback(self, button: ui.Button, inter: Interaction):
        if self.index == len(self.embeds) - 1:
            self.index = 0
        else:
            self.index += 1

        await self.button_callback(inter)

    @ui.button(emoji="🗑", style=ButtonStyle.red)
    async def button_delete_callback(self, button: ui.Button, inter: Interaction):
        self.clear_items()
        await self.button_callback(inter)

    async def on_timeout(self) -> None:
        self.clear_items()
        await self.msg.edit(embed=self.embeds[self.index], view=self)


class SelectCommand(ui.Select):
    def __init__(
        self,
        mapping: List[List[SelectOption]],
        help_command
    ):
        self.help = help_command
        self.index = 0
        self.options_list = mapping
        super().__init__(
            placeholder='⚙️More about commands',
            min_values=1, max_values=1,
            options=self.options_list[self.index],
            custom_id="command_paginator_dropdown"
        )

    def update_options(self, index):
        self.index = index
        self.options = self.options_list[self.index]

    async def callback(self, inter: Interaction):
        embed = self.help.get_command_help(self.help.context.bot.get_command(self.values[0]))
        await inter.response.send_message(
            embed=embed, ephemeral=True
        )
