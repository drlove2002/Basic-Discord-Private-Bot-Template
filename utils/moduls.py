"""
The hub for functions for random works like welcoming new member's function
can be written in here.
"""
from typing import TYPE_CHECKING

from . import logging

if TYPE_CHECKING:
    from core.bot import MainBot


logger = logging.get_logger(__name__)
