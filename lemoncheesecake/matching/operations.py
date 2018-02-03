'''
Created on Mar 27, 2017

@author: nicolas
'''

from lemoncheesecake.utils import is_string
from lemoncheesecake.runtime import log_check
from lemoncheesecake.exceptions import AbortTest, ProgrammingError
from lemoncheesecake.matching.matchers.dict_ import HasEntry, wrap_key_matcher
from lemoncheesecake.matching.matchers.composites import is_

__all__ = (
    "log_match_result",
    "check_that", "check_that_entry",
    "require_that", "require_that_entry",
    "assert_that", "assert_that_entry",
    "this_dict"
)


class _HasEntry(HasEntry):
    def description(self):
        ret = 'entry %s' % self.key_matcher.description()
        if self.value_matcher:
            ret += " " + self.value_matcher.description()
        return ret


class DictContext:
    def __init__(self, actual, base_key):
        self.actual = actual
        self.base_key = base_key


class ThisDict:
    _contexts = []

    def __init__(self, actual):
        self.context = DictContext(actual, [])

    def using_base_key(self, base_key):
        self.context.base_key = base_key if type(base_key) in (list, tuple) else [base_key]
        return self

    def __enter__(self):
        self._contexts.append(self.context)
        return self.context.actual

    def __exit__(self, type_, value, traceback):
        self._contexts.pop()

    @staticmethod
    def get_current_context():
        try:
            return ThisDict._contexts[-1]
        except IndexError:
            return None


def this_dict(actual):
    """
    Set actual to be used as implict dict in *_that_entry functions when used
    within a 'with' statement.
    """
    return ThisDict(actual)


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
    result = matcher.matches(actual)
    log_match_result(hint, matcher, result, quiet=quiet)
    return result.outcome


def check_that_entry(key_matcher, value_matcher=None, in_=None, base_key=None, quiet=False):
    """
    Helper function for check_that, takes the actual dict using in_ parameter or using 'with this_dict(...)' statement
    """
    return check_that(
        None,
        _get_actual_for_dict_operation(in_),
        _get_matcher_for_dict_operation(key_matcher, value_matcher, base_key),
        quiet=quiet
    )


def require_that(hint, actual, matcher, quiet=False):
    """Require that actual matches given matcher.

    A check log is added to the report. An AbortTest exception is raised if the check does not succeed.

    If quiet is set to True, the check details won't appear in the check log.
    """
    result = matcher.matches(actual)
    log_match_result(hint, matcher, result, quiet=quiet)
    if result.is_failure():
        raise AbortTest("previous requirement was not fulfilled")


def require_that_entry(key_matcher, value_matcher=None, in_=None, base_key=None, quiet=False):
    """
    Helper function for require_that, takes the actual dict using in_ parameter or using 'with this_dict(...)' statement
    """
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
    result = matcher.matches(actual)
    if result.is_failure():
        log_match_result(hint, matcher, result, quiet=quiet)
        raise AbortTest("assertion error")


def assert_that_entry(key_matcher, value_matcher=None, in_=None, base_key=None, quiet=False):
    """
    Helper function for assert_that, takes the actual dict using in_ parameter or using 'with this_dict(...)' statement
    """
    return assert_that(
        None,
        _get_actual_for_dict_operation(in_),
        _get_matcher_for_dict_operation(key_matcher, value_matcher, base_key),
        quiet=quiet
    )
