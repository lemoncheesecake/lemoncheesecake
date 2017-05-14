from .matchers import *
from .operations import *

DISPLAY_DETAILS_WHEN_EQUAL = True

__all__ = list(filter(lambda sym: not sym.startswith("_"), dir()))
