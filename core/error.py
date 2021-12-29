from nextcord.ext.commands import CommandError, BadArgument


class GangError(CommandError):
    """Gang error"""
    pass


class InvalidBalance(GangError):
    """Money shortage"""
    def __init__(self):
        super().__init__('You do not have sufficient balance')


class InvalidAmount(GangError):
    """Amount of money is less than equal to zero"""
    def __init__(self):
        super().__init__('Amount must be a positive non-zero number!')


class MoneyLimit(GangError):
    """In wallet we allow limited money"""
    def __init__(self):
        super().__init__('We can only allow 0 < wallet balance < 10000 and 0 < bank balance < 20000')


class GangNotFound(BadArgument):
    """Exception raised when the gang provided was not found in the bot's cache.

    This inherits from :exc:`BadArgument`

    Attributes
    -----------
    argument: :class:`str`
        The gang supplied by the caller that was not found
    """
    def __init__(self, argument: str = "") -> None:
        self.argument: str = argument
        super().__init__(f"Gang/Leader `{argument}` not found.")
