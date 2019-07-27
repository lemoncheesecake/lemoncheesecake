'''
Created on May 2, 2017

@author: nicolas
'''

from typing import Sequence, Any

from lemoncheesecake.matching.base import MatchExpected, MatchResult, match_failure, match_success, match_result, \
    got_value, serialize_values, VerbTransformation
from lemoncheesecake.matching.matchers.composites import is_


class HasItemMatchResult(MatchResult):
    def __init__(self, is_successful, description, index, item):
        MatchResult.__init__(self, is_successful, description)
        self.item = item  # type: Any
        self.index = index  # type: int

    @classmethod
    def success(cls, index, item):
        return cls(True, "found matching item at index %d" % index, index, item)

    @classmethod
    def failure(cls):
        return cls(False, "no matching item", -1, None)


class HasItem(MatchExpected):
    def build_description(self, transformation):
        return transformation(
            "to have an item whose value %s" % self.expected.build_description(VerbTransformation(conjugate=True))
        )

    def build_short_description(self, transformation):
        return transformation(
            "to have an item whose value %s" % self.expected.build_short_description(VerbTransformation(conjugate=True))
        )

    def matches(self, actual):
        for index, item in enumerate(actual):
            result = self.expected.matches(item)
            if result.is_success():
                return HasItemMatchResult.success(index, item)
        return HasItemMatchResult.failure()


def has_item(expected):
    # type: (Any) -> HasItem
    """Test if the sequence has item matching expected"""
    return HasItem(is_(expected))


class HasItems(MatchExpected):
    def build_description(self, transformation):
        return transformation("to have items %s" % serialize_values(self.expected))

    def matches(self, actual):
        missing = []
        for expected in self.expected:
            if expected not in actual:
                missing.append(expected)

        if missing:
            return match_failure("Missing items: %s" % serialize_values(missing))
        else:
            return match_success(got_value(actual))


def has_items(values):
    # type: (Sequence) -> HasItems
    """Test if the sequence contains at least the given values"""
    return HasItems(values)


class HasOnlyItems(MatchExpected):
    def build_description(self, transformation):
        return transformation("to have only items %s" % serialize_values(self.expected))

    def matches(self, actual):
        expected = list(self.expected)
        extra = []
        for value in actual:
            if value in expected:
                expected.remove(value)
            else:
                extra.append(value)

        if len(expected) == 0 and len(extra) == 0:
            return match_success(got_value(actual))
        else:
            details = []
            if len(expected) > 0:
                details.append("Missing items: %s" % serialize_values(expected))
            if len(extra) > 0:
                details.append("Extra items: %s" % serialize_values(extra))
            return match_failure("; ".join(details))


def has_only_items(expected):
    # type: (Sequence) -> HasOnlyItems
    """Test if the sequence only contains the given values"""
    return HasOnlyItems(expected)


class IsIn(MatchExpected):
    def build_description(self, transformation):
        return transformation("to be in %s" % serialize_values(self.expected))

    def matches(self, actual):
        return match_result(actual in self.expected, got_value(actual))


def is_in(expected):
    # type: (Sequence) -> IsIn
    """Test if the sequence contains the expected item"""
    return IsIn(expected)
