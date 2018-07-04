'''
Created on May 2, 2017

@author: nicolas
'''

from lemoncheesecake.matching.base import MatchExpected, MatchResult, match_failure, match_success, match_result, got_value, to_have, to_be, serialize_values
from lemoncheesecake.matching.matchers.composites import is_

__all__ = ("has_item", "has_values", "has_only_values", "is_in")


class HasItemMatchResult(MatchResult):
    def __init__(self, outcome, description, index, item):
        MatchResult.__init__(self, outcome, description)
        self.item = item
        self.index = index

    @classmethod
    def success(cls, index, item):
        return cls(True, "found matching item at index %d" % index, index, item)

    @classmethod
    def failure(cls):
        return cls(False, "no matching item", -1, None)


class HasItem(MatchExpected):
    def description(self, conjugate=False):
        return "%s an item whose value %s" % (to_have(conjugate), self.expected.description(conjugate=True))

    def short_description(self, conjugate=False):
        return "%s an item whose value %s" % (to_have(conjugate), self.expected.short_description(conjugate=True))

    def matches(self, actual):
        for index, item in enumerate(actual):
            result = self.expected.matches(item)
            if result.is_success():
                return HasItemMatchResult.success(index, item)
        return HasItemMatchResult.failure()


def has_item(expected):
    "Test if iterable has item matching expected"
    return HasItem(is_(expected))


class HasValues(MatchExpected):
    def description(self, conjugate=False):
        return "%s values %s" % (to_have(conjugate), serialize_values(self.expected))

    def matches(self, actual):
        missing = []
        for expected in self.expected:
            if expected not in actual:
                missing.append(expected)

        if missing:
            return match_failure("Missing values: %s" % serialize_values(missing))
        else:
            return match_success(got_value(actual))


def has_values(values):
    "Test if iterable contains at least the given values"
    return HasValues(values)


class HasOnlyValues(MatchExpected):
    def description(self, conjugate=False):
        return "%s only values %s" % (to_have(conjugate), serialize_values(self.expected))

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
                details.append("Missing values: %s" % serialize_values(expected))
            if len(extra) > 0:
                details.append("Extra values: %s" % serialize_values(extra))
            return match_failure("; ".join(details))


def has_only_values(values):
    "Test if iterable only contains the given values"
    return HasOnlyValues(values)


class IsIn(MatchExpected):
    def description(self, conjugate=False):
        return "%s in %s" % (to_be(conjugate), serialize_values(self.expected))

    def matches(self, actual):
        return match_result(actual in self.expected, got_value(actual))


def is_in(expected):
    return IsIn(expected)
