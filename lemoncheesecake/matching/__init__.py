from .matchers import *
from .operations import check_that, require_that, assert_that, check_that_in, require_that_in, assert_that_in

DISPLAY_DETAILS_WHEN_EQUAL = True

# for pydoc & sphinx
__all__ = [sym_name for sym_name in dir() if not sym_name.startswith("_")]
