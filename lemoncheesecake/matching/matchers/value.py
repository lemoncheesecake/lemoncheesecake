'''
Created on Mar 27, 2017

@author: nicolas
'''

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


def equal_to(expected):
    """Test if value is equal to expected"""
    return EqualTo(expected)


def _comparator(comparison_description, comparison_func):
    def wrapper(expected):
        class _Comparator(Matcher):
            def __init__(self, expected):
                self.expected = expected

            def build_description(self, transformation):
                return transformation("to be %s %s" % (comparison_description, jsonify(self.expected)))

            def matches(self, actual):
                return MatchResult(comparison_func(actual, self.expected), "got %s" % jsonify(actual))

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

    def build_description(self, transformation):
        return transformation("to be between %s and %s" % (self.min, self.max))

    def matches(self, actual):
        return MatchResult(self.min <= actual <= self.max, "got %s" % jsonify(actual))


def is_between(min, max):
    # type: (float, float) -> IsBetween
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


def is_none():
    """Test if value is None"""
    return IsNone()


def is_not_none():
    """Test if value is not None"""
    return not_(is_none())


class HasLength(Matcher):
    def __init__(self, matcher):
        # type: (Matcher) -> None
        self.matcher = matcher

    def build_description(self, transformation):
        return transformation(
            "to have a length that %s" % (self.matcher.build_description(MatcherDescriptionTransformer(conjugate=True)))
        )

    def matches(self, actual):
        return self.matcher.matches(len(actual))


def has_length(length):
    # type: (int) -> HasLength
    """Test if value has a length of"""
    return HasLength(is_(length))


def is_true():
    """Test if value is true (boolean type)"""
    return is_bool(True)


def is_false():
    """Test if value is false (boolean type)"""
    return is_bool(False)
