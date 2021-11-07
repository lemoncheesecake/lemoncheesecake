'''
Created on Mar 27, 2017

@author: nicolas
'''

from typing import Any, Mapping, Sequence, Optional, Union
import six

from lemoncheesecake.session import log_check
from lemoncheesecake.exceptions import AbortTest
from lemoncheesecake.matching.matcher import Matcher, MatchResult, MatcherDescriptionTransformer
from lemoncheesecake.matching.matchers.dict_ import HasEntry, KeyPathMatcher


class _HasEntry(HasEntry):
    def build_description(self, _):
        ret = self.key_matcher.build_description()
        if self.value_matcher:
            ret += " " + self.value_matcher.build_description(MatcherDescriptionTransformer())
        return ret


def _build_has_entry_matchers_from_arg(arg, path=()):
    if isinstance(arg, (list, tuple)):
        for idx, value in enumerate(arg):
            for matcher in _build_has_entry_matchers_from_arg(value, path + (idx,)):
                yield matcher

    elif isinstance(arg, dict):
        for key, value in arg.items():
            for matcher in _build_has_entry_matchers_from_arg(value, path + (key,)):
                yield matcher

    elif isinstance(arg, Matcher):
        yield _HasEntry(KeyPathMatcher(path), arg)

    else:
        raise ValueError("argument %r must be either an instance of list, tuple, dict or Matcher" % arg)


def _normalize_key_path(path):
    if isinstance(path, tuple):
        return path
    elif isinstance(path, list):
        return tuple(path)
    else:
        return (path,)


def _build_has_entry_matchers_from_args(args, base_key=()):
    base_key = _normalize_key_path(base_key)

    if len(args) == 1:
        assert isinstance(args[0], (list, tuple, dict))
        for matcher in _build_has_entry_matchers_from_arg(args[0], base_key):
            yield matcher

    elif len(args) % 2 == 0:
        i = 0
        while i < len(args):
            key, value_matcher = args[i], args[i + 1]
            for matcher in _build_has_entry_matchers_from_arg(value_matcher, base_key + _normalize_key_path(key)):
                yield matcher
            i += 2

    else:
        raise ValueError(
            "*args must be a list of one element (being a list/tuple/dict) or "
            "a even number list (a list of key/matcher pairs)"
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
    # type: (Optional[str], Any, Matcher, bool) -> MatchResult

    """Check that actual matches given matcher.

    A check log is added to the report.

    If ``quiet`` is set to ``True``, the check details won't appear in the check log.
    """
    assert isinstance(matcher, Matcher)

    result = matcher.matches(actual)
    _log_match_result(hint, matcher, result, quiet=quiet)
    return result


def check_that_in(actual, *expected, **kwargs):
    # type: (Mapping, Any, Any) -> Sequence[MatchResult]

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

    .. versionadded:: 1.11.0

    Nested data can also be checked this way::

        check_that_in(
            {"foo": {"bar": 2}},
            {"foo": {"bar": equal_to(2)}}
        )

    It also means that instead of calling ``check_that_in`` with a list of key/matcher pairs, it can now
    be called with a data structure as the "expected" argument.
    """
    quiet = kwargs.get("quiet", False)
    base_key = kwargs.get("base_key", ())

    return [
        check_that(None, actual, matcher, quiet=quiet)
        for matcher in _build_has_entry_matchers_from_args(expected, base_key)
    ]


def require_that_in(actual, *expected, **kwargs):
    # type: (Mapping, Any, Any) -> Sequence[MatchResult]

    """
    Does the same thing as :py:func:`check_that_in` except it performs a
    :py:func:`require_that` on each key-matcher pair.
    """
    quiet = kwargs.get("quiet", False)
    base_key = kwargs.get("base_key", ())

    return [
        require_that(None, actual, matcher, quiet=quiet)
        for matcher in _build_has_entry_matchers_from_args(expected, base_key)
    ]


def assert_that_in(actual, *expected, **kwargs):
    # type: (Mapping, Any, Any) -> Sequence[MatchResult]

    """
    Does the same thing as :py:func:`check_that_in` except it performs a
    :py:func:`assert_that` on each key-matcher pair.
    """
    quiet = kwargs.get("quiet", False)
    base_key = kwargs.get("base_key", ())

    return [
        assert_that(None, actual, matcher, quiet=quiet)
        for matcher in _build_has_entry_matchers_from_args(expected, base_key)
    ]


def require_that(hint, actual, matcher, quiet=False):
    # type: (Optional[str], Any, Matcher, bool) -> MatchResult

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
    # type: (Optional[str], Any, Matcher, bool) -> MatchResult

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
