'''
Created on Apr 4, 2017

@author: nicolas
'''

import os
import re
import difflib
import json

from typing import Any, Pattern, Union, Callable

from lemoncheesecake.matching.base import MatchExpected, MatchResult, got_value

_REGEXP_TYPE = type(re.compile(r"dummy"))


class StartsWith(MatchExpected):
    def build_description(self, transformation):
        return transformation('to start with "%s"' % self.expected)

    def matches(self, actual):
        return MatchResult(actual.startswith(self.expected), got_value(actual))


def starts_with(expected):
    # type: (str) -> StartsWith
    """Test if string begins with given prefix"""
    return StartsWith(expected)


class EndsWith(MatchExpected):
    def build_description(self, transformation):
        return transformation('to end with "%s"' % self.expected)

    def matches(self, actual):
        return MatchResult(actual.endswith(self.expected), got_value(actual))


def ends_with(expected):
    # type: (str) -> EndsWith
    """Test if string ends with given suffix"""
    return EndsWith(expected)


class ContainsString(MatchExpected):
    def build_description(self, transformation):
        return transformation('to contain "%s"' % self.expected)

    def matches(self, actual):
        return MatchResult(self.expected in actual, got_value(actual))


def contains_string(expected):
    # type: (str) -> ContainsString
    """Test if string contains sub string"""
    return ContainsString(expected)


class MatchPattern(MatchExpected):
    def __init__(self, expected, description=None, mention_regexp=False):
        MatchExpected.__init__(self, expected)
        assert not (mention_regexp and description is None)
        self._description = description
        self._mention_regexp = mention_regexp

    def build_description(self, transformation):
        if self._description:
            desc = transformation("to be %s" % self._description)
            if self._mention_regexp:
                desc += ' (pattern: "%s")' % self.expected.pattern
            return desc
        else:
            return transformation('to match pattern "%s"' % self.expected.pattern)

    def matches(self, actual):
        try:
            match = self.expected.search(actual)
        except TypeError:
            return MatchResult.failure("Invalid value %s (%s)" % (repr(actual), type(actual)))
        return MatchResult(match is not None, got_value(actual))


def match_pattern(pattern, description=None, mention_regexp=False):
    # type: (Union[str, Pattern], str, bool) -> MatchPattern
    """Test if string matches given pattern (using the `search` method of the `re` module)"""
    return MatchPattern(
        pattern if type(pattern) == _REGEXP_TYPE else re.compile(pattern), description, mention_regexp
    )


def make_pattern_matcher(pattern, description=None, mention_regexp=False):
    # type: (Union[str, Pattern], str, bool) -> Callable[[], MatchPattern]
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

    def build_description(self, transformation):
        return transformation("to be the text:\n<<<\n%s\n>>>\n" % self.expected)

    def matches(self, actual):
        if actual == self.expected:
            return MatchResult.success()
        else:
            return MatchResult.failure(
                "Text does not match:\n%s" % _diff_text(self.expected, actual, self.linesep)
            )


def is_text(expected, linesep=os.linesep):
    # type: (str, str) -> IsText
    """
    Test if the two multi-lines texts match.

    If the two values do not match, the match result description will be a diff between the two texts.
    """
    return IsText(expected, linesep)


def _format_json(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=4)


class IsJson(MatchExpected):
    def build_description(self, transformation):
        return transformation("to be the JSON:\n%s\n" % _format_json(self.expected))

    def matches(self, actual):
        if actual == self.expected:
            return MatchResult.success()
        else:
            return MatchResult.failure(
                "JSON does not match:\n%s" % _diff_text(_format_json(self.expected), _format_json(actual), "\n")
            )


def is_json(expected):
    # type: (Any) -> IsJson
    """
    Test if the two data structures (that can be represented as JSON) match.

    If the two values do not match, the match result description will be a textual diff between the two JSON
    representations.
    """
    return IsJson(expected)
