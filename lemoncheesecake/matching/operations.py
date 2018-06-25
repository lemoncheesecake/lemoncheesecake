'''
Created on Mar 27, 2017

@author: nicolas
'''

import threading

from lemoncheesecake.utils import is_string
from lemoncheesecake.runtime import log_check
from lemoncheesecake.exceptions import AbortTest, ProgrammingError
from lemoncheesecake.matching.base import Matcher
from lemoncheesecake.matching.matchers.dict_ import HasEntry, wrap_key_matcher
from lemoncheesecake.matching.matchers.composites import is_

__all__ = (
    "log_match_result",
    "check_that", "check_that_entry", "check_that_in",
    "require_that", "require_that_entry", "require_that_in",
    "assert_that", "assert_that_entry", "assert_that_in",
    "this_dict"
)


class _HasEntry(HasEntry):
    def description(self):
        ret = self.key_matcher.description()
        if self.value_matcher:
            ret += " " + self.value_matcher.description()
        return ret


class DictContext:
    def __init__(self, actual, base_key):
        self.actual = actual
        self.base_key = base_key


class ThisDict(object):
    _local = threading.local()
    _local.contexts = []

    def __init__(self, actual):
        self.context = DictContext(actual, [])

    def using_base_key(self, base_key):
        self.context.base_key = base_key if type(base_key) in (list, tuple) else [base_key]
        return self

    def __enter__(self):
        try:
            self._local.contexts.append(self.context)
        except AttributeError:
            self._local.contexts = [self.context]
        return self.context.actual

    def __exit__(self, type_, value, traceback):
        self._local.contexts.pop()

    @staticmethod
    def get_current_context():
        try:
            return ThisDict._local.contexts[-1]
        except (IndexError, AttributeError):
            return None


def this_dict(actual):
    """
    Set actual to be used as implicit dict in *_that_entry functions when used
    within a 'with' statement.
    """
    return ThisDict(actual)


def _is_matcher(obj):
    return isinstance(obj, Matcher)


def _get_actual_for_dict_operation(in_):
    if in_ is not None:
        return in_
    else:
        context = ThisDict.get_current_context()
        if not context:
            raise ProgrammingError(
                "Actual dict must be set either using in_ argument or using 'with this_dict(...)' statement"
            )
        return context.actual


def _get_matcher_for_dict_operation(key_matcher, value_matcher, base_key):
    if base_key is None:
        context = ThisDict.get_current_context()
        base_key = context.base_key if context is not None else []

    return _HasEntry(
        wrap_key_matcher(key_matcher, base_key=base_key),
        value_matcher if value_matcher is not None else is_(value_matcher)
    )


def format_result_details(details):
    if details is None:
        return None

    if not is_string(details):
        details = str(details)

    return details[0].upper() + details[1:]


def log_match_result(hint, matcher, result, quiet=False):
    """Add a check log to the report.

    If quiet is set to True, the check details won't appear in the check log.
    """
    if hint is not None:
        description = "Expect %s %s" % (hint, matcher.description())
    else:
        description = "Expect %s" % matcher.description()

    return log_check(
        description, result.outcome, format_result_details(result.description) if not quiet else None
    )


def check_that(hint, actual, matcher, quiet=False):
    """Check that actual matches given matcher.

    A check log is added to the report.

    If quiet is set to True, the check details won't appear in the check log.
    """
    assert _is_matcher(matcher)

    result = matcher.matches(actual)
    log_match_result(hint, matcher, result, quiet=quiet)
    return result


def check_that_entry(key_matcher, value_matcher=None, in_=None, base_key=None, quiet=False):
    """
    Helper function for check_that, takes the actual dict using in_ parameter or using 'with this_dict(...)' statement
    """
    assert value_matcher is None or _is_matcher(value_matcher)

    return check_that(
        None,
        _get_actual_for_dict_operation(in_),
        _get_matcher_for_dict_operation(key_matcher, value_matcher, base_key),
        quiet=quiet
    )


def _do_that_in(func, actual, *args, **kwargs):
    if len(args) % 2 != 0:
        raise TypeError("function expects an even number of *args")

    base_key = kwargs.get("base_key", [])
    quiet = kwargs.get("quiet", False)

    results = []
    i = 0
    while i < len(args):
        key, value_matcher = args[i], args[i+1]
        result = func(key, value_matcher, in_=actual, base_key=base_key, quiet=quiet)
        results.append(result)
        i += 2

    return results


def check_that_in(actual, *args, **kwargs):
    return _do_that_in(check_that_entry, actual, *args, **kwargs)


def require_that_in(actual, *args, **kwargs):
    return _do_that_in(require_that_entry, actual, *args, **kwargs)


def assert_that_in(actual, *args, **kwargs):
    return _do_that_in(assert_that_entry, actual, *args, **kwargs)


def require_that(hint, actual, matcher, quiet=False):
    """Require that actual matches given matcher.

    A check log is added to the report. An AbortTest exception is raised if the check does not succeed.

    If quiet is set to True, the check details won't appear in the check log.
    """
    assert _is_matcher(matcher)

    result = matcher.matches(actual)
    log_match_result(hint, matcher, result, quiet=quiet)
    if result:
        return result
    else:
        raise AbortTest("previous requirement was not fulfilled")


def require_that_entry(key_matcher, value_matcher=None, in_=None, base_key=None, quiet=False):
    """
    Helper function for require_that, takes the actual dict using in_ parameter or using 'with this_dict(...)' statement
    """
    assert value_matcher is None or _is_matcher(value_matcher)

    return require_that(
        None,
        _get_actual_for_dict_operation(in_),
        _get_matcher_for_dict_operation(key_matcher, value_matcher, base_key),
        quiet=quiet
    )


def assert_that(hint, actual, matcher, quiet=False):
    """Assert that actual matches given matcher.

    If assertion fail, a check log is added to the report and an AbortTest exception is raised.

    If quiet is set to True, the check details won't appear in the check log.
    """
    assert _is_matcher(matcher)

    result = matcher.matches(actual)
    if result:
        return result
    else:
        log_match_result(hint, matcher, result, quiet=quiet)
        raise AbortTest("assertion error")


def assert_that_entry(key_matcher, value_matcher=None, in_=None, base_key=None, quiet=False):
    """
    Helper function for assert_that, takes the actual dict using in_ parameter or using 'with this_dict(...)' statement
    """
    assert value_matcher is None or _is_matcher(value_matcher)

    return assert_that(
        None,
        _get_actual_for_dict_operation(in_),
        _get_matcher_for_dict_operation(key_matcher, value_matcher, base_key),
        quiet=quiet
    )
