'''
Created on Mar 27, 2017

@author: nicolas
'''

from typing import Union, Any

from lemoncheesecake.helpers.text import jsonify
from lemoncheesecake.matching.matcher import Matcher, MatchResult, MatcherDescriptionTransformer
from lemoncheesecake.matching.matchers.composites import is_, not_
from lemoncheesecake.matching.matchers.types_ import is_bool


class EqualTo(Matcher):
    def __init__(self, expected):
        self.expected = expected

    def build_description(self, transformation):
        return transformation("to be equal to %s" % jsonify(self.expected))

    def matches(self, actual):
        from lemoncheesecake.matching import DISPLAY_DETAILS_WHEN_EQUAL

        if actual == self.expected:
            if DISPLAY_DETAILS_WHEN_EQUAL:
                return MatchResult.success("got %s" % jsonify(actual))
            else:
                return MatchResult.success()
        else:
            return MatchResult.failure("got %s" % jsonify(actual))


def equal_to(expected: Any) -> Matcher:
    """Test if value is equal to expected"""
    return EqualTo(expected)


class _Comparator(Matcher):
    def __init__(self, expected, comparison, comparison_description):
        self.expected = expected
        self.comparison = comparison
        self.comparison_description = comparison_description

    def build_description(self, transformation):
        return transformation("to be %s %s" % (self.comparison_description, jsonify(self.expected)))

    def matches(self, actual):
        return MatchResult(self.comparison(actual, self.expected), f"got {jsonify(actual)}")


def not_equal_to(expected: Any) -> Matcher:
    """
    Test if value is not equal to expected.
    """
    return _Comparator(expected, lambda a, e: a != e, "not equal to")


def greater_than(expected: Any) -> Matcher:
    """
    Test if value is greater than expected.
    """
    return _Comparator(expected, lambda a, e: a > e, "greater than")


def greater_than_or_equal_to(expected: Any) -> Matcher:
    """
    Test if value is greater than or equal to expected.
    """
    return _Comparator(expected, lambda a, e: a >= e, "greater than or equal to")


def less_than(expected: Any) -> Matcher:
    """
    Test if value is less than expected.
    """
    return _Comparator(expected, lambda a, e: a < e, "less than")


def less_than_or_equal_to(expected: Any) -> Matcher:
    """
    Test if value is less than or equal to expected.
    """
    return _Comparator(expected, lambda a, e: a <= e, "less than or equal to")


class IsBetween(Matcher):
    def __init__(self, min, max):
        self.min = min
        self.max = max

    def build_description(self, transformation):
        return transformation("to be between %s and %s" % (self.min, self.max))

    def matches(self, actual):
        return MatchResult(self.min <= actual <= self.max, "got %s" % jsonify(actual))


def is_between(min: Union[int, float], max: Union[int, float]) -> Matcher:
    """Test if value is between min and max"""
    return IsBetween(min, max)


class IsNone(Matcher):
    def build_description(self, transformation):
        return transformation("to be null")

    def matches(self, actual):
        if actual is None:
            return MatchResult.success("got null")
        else:
            return MatchResult.failure("got %s" % jsonify(actual))


def is_none() -> Matcher:
    """Test if value is None"""
    return IsNone()


def is_not_none() -> Matcher:
    """Test if value is not None"""
    return not_(is_none())


class HasLength(Matcher):
    def __init__(self, matcher: Matcher) -> None:
        self.matcher = matcher

    def build_description(self, transformation):
        return transformation(
            "to have a length that %s" % (self.matcher.build_description(MatcherDescriptionTransformer(conjugate=True)))
        )

    def matches(self, actual):
        return self.matcher.matches(len(actual))


def has_length(length: Union[int, Matcher]) -> Matcher:
    """Test if value has a length of"""
    return HasLength(is_(length))


def is_true() -> Matcher:
    """Test if value is true (boolean type)"""
    return is_bool(True)


def is_false() -> Matcher:
    """Test if value is false (boolean type)"""
    return is_bool(False)
