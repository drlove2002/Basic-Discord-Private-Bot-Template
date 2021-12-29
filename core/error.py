from nextcord.ext.commands import CommandError


class CustomError(CommandError):
    """This is a  Custom Error class inherited from CommandError"""
    pass


class InvalidBalance(CustomError):
    """Money shortage"""
    def __init__(self):
        super().__init__('You do not have sufficient balance')


class InvalidAmount(CustomError):
    """Amount of money is less than equal to zero"""
    def __init__(self):
        super().__init__('Amount must be a positive non-zero number!')


class MoneyLimit(CustomError):
    """In wallet we allow limited money"""
    def __init__(self):
        super().__init__('We can only allow 0 < wallet balance < 10000 and 0 < bank balance < 20000')
