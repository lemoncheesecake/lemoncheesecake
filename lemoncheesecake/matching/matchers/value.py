'''
Created on Mar 27, 2017

@author: nicolas
'''

from lemoncheesecake.matching.base import (
    MatchExpected, Matcher, match_result, match_success, match_failure,
    got_value, serialize_value, to_be, to_have
)
from lemoncheesecake.matching.matchers.composites import is_
from lemoncheesecake.matching.matchers.types_ import is_bool


class EqualTo(MatchExpected):
    def build_description(self, conjugate=False):
        return "%s equal to %s" % (to_be(conjugate), serialize_value(self.expected))

    def matches(self, actual):
        from lemoncheesecake.matching import DISPLAY_DETAILS_WHEN_EQUAL

        if actual == self.expected:
            return match_success(got_value(actual)) if DISPLAY_DETAILS_WHEN_EQUAL else match_success()
        else:
            return match_failure(got_value(actual))


def equal_to(expected):
    """Test if value is equal to expected"""
    return EqualTo(expected)


def _comparator(comparison_description, comparison_func):
    def wrapper(expected):
        class _Comparator(MatchExpected):
            def build_description(self, conjugate=False):
                return "%s %s %s" % (to_be(conjugate), comparison_description, serialize_value(self.expected))

            def matches(self, actual):
                return match_result(comparison_func(actual, self.expected), got_value(actual))

        return _Comparator(expected)

    wrapper.__doc__ = """Test if value is %s expected""" % comparison_description
    return wrapper


not_equal_to = _comparator("not equal to", lambda a, e: a != e)

greater_than = _comparator("greater than", lambda a, e: a > e)
greater_than_or_equal_to = _comparator("greater than or equal to", lambda a, e: a >= e)

less_than = _comparator("less than", lambda a, e: a < e)
less_than_or_equal_to = _comparator("greater than or equal to", lambda a, e: a <= e)


class IsBetween(Matcher):
    def __init__(self, min, max):
        self.min = min
        self.max = max

    def build_description(self, conjugate=False):
        return "%s between %s and %s" % (to_be(conjugate), self.min, self.max)

    def matches(self, actual):
        return match_result(self.min <= actual <= self.max, got_value(actual))


def is_between(min, max):
    """Test if value is between min and max"""
    return IsBetween(min, max)


def is_none():
    """Test if value is None"""
    return equal_to(None)


def is_not_none():
    """Test if value is not None"""
    return not_equal_to(None)


class HasLength(Matcher):
    def __init__(self, matcher):
        # type: (Matcher) -> None
        self.matcher = matcher

    def build_description(self, conjugate=False):
        return "%s a length that %s" % (to_have(conjugate), self.matcher.build_description(conjugate=True))

    def matches(self, actual):
        return self.matcher.matches(len(actual))


def has_length(length):
    """Test if value has a length of"""
    return HasLength(is_(length))


def is_true():
    """Test if value is true (boolean type)"""
    return is_bool(True)


def is_false():
    """Test if value is false (boolean type)"""
    return is_bool(False)
