'''
Created on Mar 27, 2017

@author: nicolas
'''

from typing import Any, Mapping, List
import six

from lemoncheesecake.session import log_check
from lemoncheesecake.exceptions import AbortTest
from lemoncheesecake.matching.matcher import Matcher, MatchResult, MatcherDescriptionTransformer
from lemoncheesecake.matching.matchers.dict_ import HasEntry, wrap_key_matcher
from lemoncheesecake.matching.matchers.composites import is_


class _HasEntry(HasEntry):
    def build_description(self, _):
        ret = self.key_matcher.build_description()
        if self.value_matcher:
            ret += " " + self.value_matcher.build_description(MatcherDescriptionTransformer())
        return ret


def _build_matcher_for_dict_operation(key_matcher, value_matcher, base_key):
    return _HasEntry(
        wrap_key_matcher(key_matcher, base_key=base_key),
        value_matcher if value_matcher is not None else is_(value_matcher)
    )


def _format_result_details(details):
    if details is None:
        return None

    if not isinstance(details, six.string_types):
        details = str(details)

    return details[0].upper() + details[1:]


def _log_match_result(hint, matcher, result, quiet=False):
    if hint is not None:
        description = "Expect %s %s" % (hint, matcher.build_description(MatcherDescriptionTransformer()))
    else:
        description = "Expect %s" % matcher.build_description(MatcherDescriptionTransformer())

    return log_check(
        description, result.is_successful, _format_result_details(result.description) if not quiet else None
    )


def check_that(hint, actual, matcher, quiet=False):
    # type: (str, Any, Matcher, bool) -> MatchResult

    """Check that actual matches given matcher.

    A check log is added to the report.

    If ``quiet`` is set to ``True``, the check details won't appear in the check log.
    """
    assert isinstance(matcher, Matcher)

    result = matcher.matches(actual)
    _log_match_result(hint, matcher, result, quiet=quiet)
    return result


def _do_that_in(func, actual, *args, **kwargs):
    if len(args) % 2 != 0:
        raise TypeError("function expects an even number of *args")

    for value_matcher in args[1::2]:  # iterate over each odd element
        assert value_matcher is None or isinstance(value_matcher, Matcher)

    base_key = kwargs.get("base_key", [])
    quiet = kwargs.get("quiet", False)

    results = []
    i = 0
    while i < len(args):
        key_matcher, value_matcher = args[i], args[i+1]
        result = func(
            None, actual, _build_matcher_for_dict_operation(key_matcher, value_matcher, base_key), quiet=quiet
        )
        results.append(result)
        i += 2

    return results


def check_that_in(actual, *args, **kwargs):
    # type: (Mapping, Any, Any) -> List[MatchResult]

    """
    Equivalent of :py:func:`check_that` over items of a dict.

    Example of usage::

        check_that_in(
            {"foo": 1, "bar": 2},
            "foo", equal_to(1),
            "bar", equal_to(2)
        )

    The key can also be a ``tuple`` when checking for a nested item::

        check_that_in(
            {"foo": {"bar": 2}},
            ("foo", "bar"), equal_to(2)
        )

    The function can take a ``base_key`` keyword-arg to pass repeating nested-keys as a ``tuple``.

    If an extra ``quiet`` keyword-arg is set to ``True``, the check details won't appear in the check log.

    The function returns a list of :py:class:`MatchResult <lemoncheesecake.matching.matcher.MatchResult>`.
    """

    return _do_that_in(check_that, actual, *args, **kwargs)


def require_that_in(actual, *args, **kwargs):
    # type: (Mapping, Any, Any) -> List[MatchResult]

    """
    Does the same thing as :py:func:`check_that_in` except it performs a
    :py:func:`require_that` on each key-value pair.
    """

    return _do_that_in(require_that, actual, *args, **kwargs)


def assert_that_in(actual, *args, **kwargs):
    # type: (Mapping, Any, Any) -> List[MatchResult]

    """
    Does the same thing as :py:func:`check_that_in` except it performs a
    :py:func:`assert_that` on each key-value pair.
    """

    return _do_that_in(assert_that, actual, *args, **kwargs)


def require_that(hint, actual, matcher, quiet=False):
    # type: (str, Any, Matcher, bool) -> MatchResult

    """Require that actual matches given matcher.

    A check log is added to the report. An AbortTest exception is raised if the check does not succeed.

    If ``quiet`` is set to ``True``, the check details won't appear in the check log.
    """
    assert isinstance(matcher, Matcher)

    result = matcher.matches(actual)
    _log_match_result(hint, matcher, result, quiet=quiet)
    if result:
        return result
    else:
        raise AbortTest("previous requirement was not fulfilled")


def assert_that(hint, actual, matcher, quiet=False):
    # type: (str, Any, Matcher, bool) -> MatchResult

    """Assert that actual matches given matcher.

    If assertion fail, a check log is added to the report and an AbortTest exception is raised.

    If ``quiet`` is set to ``True``, the check details won't appear in the check log.
    """
    assert isinstance(matcher, Matcher)

    result = matcher.matches(actual)
    if result:
        return result
    else:
        _log_match_result(hint, matcher, result, quiet=quiet)
        raise AbortTest("assertion error")
