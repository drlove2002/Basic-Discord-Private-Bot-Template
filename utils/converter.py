import re
from typing import TYPE_CHECKING, Optional

from nextcord.ext.commands import Context, Converter, UserInputError

if TYPE_CHECKING:
    UrlParser = str
else:
    class UrlParser(Converter):
        def __init__(self):
            self.__ext = ('webp', 'png', 'jpg', 'jpeg', 'jpe', 'jif', 'jfif', 'jfi')
            self.__pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

        async def convert(self, ctx: Optional[Context], argument: str) -> str:
            urls = re.findall(self.__pattern, argument)
            if urls and any([urls[0].lower().endswith(f".{e}") for e in self.__ext]):
                return urls[0]
            raise UserInputError("Insufficient Image Url!")
