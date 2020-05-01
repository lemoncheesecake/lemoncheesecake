import inspect

from .matchers import *
from .operations import check_that, require_that, assert_that, check_that_in, require_that_in, assert_that_in

DISPLAY_DETAILS_WHEN_EQUAL = True


def _is_symbol_exportable(sym_name):
    return all((
        sym_name != "DISPLAY_DETAILS_WHEN_EQUAL",
        not sym_name.startswith("_"),
        not inspect.ismodule(globals()[sym_name])
    ))


__all__ = list(filter(_is_symbol_exportable, dir()))
