'''
Created on Apr 4, 2017

@author: nicolas
'''

import os
import re
import difflib
import json


from lemoncheesecake.matching.base import MatchExpected, match_result, match_success, match_failure, got_value, to_be

__all__ = (
    "starts_with", "ends_with", "contains_string", "match_pattern", "is_text", "is_json"
)

_REGEXP_TYPE = type(re.compile("dummy"))


class StartsWith(MatchExpected):
    def description(self, conjugate=False):
        return '%s with "%s"' % ("starts" if conjugate else "to start", self.expected)

    def matches(self, actual):
        return match_result(actual.startswith(self.expected), got_value(actual))


def starts_with(s):
    """Test if string begins with given prefix"""
    return StartsWith(s)


class EndsWith(MatchExpected):
    def description(self, conjugate=False):
        return '%s with "%s"' % ("ends" if conjugate else "to end", self.expected)

    def matches(self, actual):
        return match_result(actual.endswith(self.expected), got_value(actual))


def ends_with(s):
    """Test if string ends with given suffix"""
    return EndsWith(s)


class ContainsString(MatchExpected):
    def description(self, conjugate=False):
        return '%s "%s"' % ("contains" if conjugate else "to contain", self.expected)

    def matches(self, actual):
        return match_result(self.expected in actual, got_value(actual))


def contains_string(s):
    """Test if string contains sub string"""
    return ContainsString(s)


class MatchPattern(MatchExpected):
    def __init__(self, expected, description=None, mention_regexp=False):
        MatchExpected.__init__(self, expected)
        assert not (mention_regexp and description is None)
        self._description = description
        self._mention_regexp = mention_regexp

    def description(self, conjugate=False):
        if self._description:
            desc = "%s %s" % (to_be(conjugate), self._description)
            if self._mention_regexp:
                desc += ' (pattern: "%s")' % self.expected.pattern
            return desc
        else:
            return '%s "%s"' % ("matches pattern" if conjugate else "to match pattern", self.expected.pattern)

    def matches(self, actual):
        try:
            match = self.expected.search(actual)
        except TypeError:
            return match_failure("Invalid value %s (%s)" % (repr(actual), type(actual)))
        return match_result(match is not None, got_value(actual))


def match_pattern(pattern, description=None, mention_regexp=False):
    """Test if string matches given pattern (using the `search` method of the `re` module)"""
    return MatchPattern(
        pattern if type(pattern) == _REGEXP_TYPE else re.compile(pattern), description, mention_regexp
    )


def make_pattern_matcher(pattern, description=None, mention_regexp=False):
    def matcher():
        return match_pattern(pattern, description, mention_regexp)
    return matcher


def _diff_text(text1, text2, linesep):
    return "\n".join(
        difflib.unified_diff(
            text1.split(linesep), text2.split(linesep), fromfile="expected", tofile="actual", lineterm=""
        )
    )


class IsText(MatchExpected):
    def __init__(self, expected, linesep):
        MatchExpected.__init__(self, expected)
        self.linesep = linesep

    def description(self, conjugate=False):
        return "%s the text:\n<<<\n%s\n>>>\n" % (to_be(conjugate), self.expected)

    def matches(self, actual):
        if actual == self.expected:
            return match_success()
        else:
            return match_failure(
                "Text does not match:\n%s" % _diff_text(self.expected, actual, self.linesep)
            )


def is_text(expected, linesep=os.linesep):
    return IsText(expected, linesep)


def _format_json(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=4)


class IsJson(MatchExpected):
    def description(self, conjugate=False):
        return "%s JSON:\n%s\n" % (to_be(conjugate), _format_json(self.expected))

    def matches(self, actual):
        if actual == self.expected:
            return match_success()
        else:
            return match_failure(
                "JSON does not match:\n%s" % _diff_text(_format_json(self.expected), _format_json(actual), "\n")
            )


def is_json(expected):
    return IsJson(expected)
