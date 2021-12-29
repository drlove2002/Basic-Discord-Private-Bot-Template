from random import randint
from textwrap import dedent

from nextcord import Embed, SelectOption
from nextcord.ext import commands
from nextcord.utils import as_chunks

from utils.checks import is_invoked_with_command
from .constants import COMMAND_CHANNELS, EMOJI
from .pawgenator import Paginator
from utils.util import Raise


class EmbedHelpCommand(commands.HelpCommand):
    """This is an HelpCommand that utilizes embeds."""

    def __init__(self):
        super().__init__()
        self.per_page_items = 6

    def get_command_signature(self, command):
        return '{0.qualified_name} {0.signature}'.format(command)

    @staticmethod
    def get_command_description(command):
        return command.description or command.short_doc or command.help or "No Description"

    def get_command_help(self, command) -> Embed:
        return Embed(
            title=f"Command: {command.name}",
            description=dedent(f"""\
            **:bulb: Description**
            ```ini
            [{self.get_command_description(command)}]
            ```
            **:video_game: Usage**: `{self.context.prefix}{command.name} {command.usage or ''}`
            **:video_game: Aliases**: `{command.aliases}`
            """),
            colour=randint(0x000000, 0xFFFFFF))

    async def send_bot_help(self, mapping):
        pages, options_list = [], []
        ctx = self.context
        for cog, cmds in mapping.items():
            cog_name = 'No Category' if cog is None else cog.qualified_name
            filtered = await self.filter_commands(cmds, sort=True)
            if not filtered:
                continue
            for chunk in as_chunks(filtered, self.per_page_items):
                options = []
                embed = (
                    Embed(
                        color=randint(0x000000, 0xFFFFFF),
                        title=f"**⚙️ {cog_name}**",
                        description=cog.description if cog else Embed.Empty, ).set_footer(
                        text=f"Type {ctx.prefix}help <command> for more info",
                        icon_url=ctx.author.display_avatar.url,
                    )
                )
                for c in chunk:
                    c_usage = c.usage or ""
                    title = f"`{ctx.prefix}{c.name} {c_usage}`"
                    embed.add_field(
                        name=title,
                        value=f"{EMOJI.DOT} {self.get_command_description(c)}",
                        inline=False)
                    options.append(SelectOption(
                        value=c.name, label=c.name,
                        description=self.get_command_description(c))
                    )
                pages.append(embed)
                options_list.append(options)
        paginator = Paginator(channel=ctx.channel, user=ctx.author, embeds=pages)
        await paginator.add_dropdown(options_list, self)
        await paginator.start()

    async def send_cog_help(self, cog):
        ctx = self.context
        destination = self.get_destination()
        embed = Embed(
            color=randint(0x000000, 0xFFFFFF),
            title=f"⚙️{cog.qualified_name}",
            description=cog.description or Embed.Empty,
        ).set_footer(
            text=f"Type {ctx.prefix}help <command> for more help",
            icon_url=ctx.author.display_avatar.url,
        )
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        if not filtered:
            return await Raise(ctx, f"Command or category not found. Use {ctx.prefix}help", delete_after=10).error()
        for c in filtered:
            desc = c.short_doc or c.description or "No Description"
            c_usage = c.usage or ""
            title = f"`{ctx.prefix}{c.name} {c_usage}`"
            embed.add_field(name=title, value=f"{EMOJI.DOT} {desc}", inline=False)
        await destination.send(embed=embed, delete_after=None if destination.id in COMMAND_CHANNELS else 30)

    async def send_group_help(self, group):
        ctx = self.context
        destination = self.get_destination()
        embed = Embed(
            color=randint(0x000000, 0xFFFFFF),
            title=f"⚙️{group.qualified_name}",
            description=group.description or Embed.Empty,
        ).set_footer(
            text=f"Type {ctx.prefix}help <command> for more help",
            icon_url=ctx.author.display_avatar.url,
        )
        for c in sorted(set(group.commands), key=lambda cmd: cmd.name):
            if c.hidden or c.parent:
                continue
            desc = c.short_doc or c.description or "No Description"
            c_usage = c.usage or ""
            title = f"`{ctx.prefix}{c.name} {c_usage}`"
            embed.add_field(name=title, value=f"{EMOJI.DOT} {desc}", inline=False)
        await destination.send(embed=embed, delete_after=None if destination.id in COMMAND_CHANNELS else 20)

    async def send_command_help(self, command):
        if command.hidden:
            return
        embed = self.get_command_help(command)
        destination = self.get_destination()
        if not is_invoked_with_command(self.context):
            return await destination.send(embed=embed, delete_after=10)
        await destination.send(embed=embed, delete_after=None if destination.id in COMMAND_CHANNELS else 20)
