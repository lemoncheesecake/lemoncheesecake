'''
Created on Mar 28, 2017

@author: nicolas
'''

from typing import List, Any

from lemoncheesecake.matching.base import Matcher, match_success, match_failure, match_result, \
    got, got_value, to_be, merge_match_result_descriptions


def _make_item(content, prefix="- "):
    lines = content.split("\n")
    return "\n".join(
        ["    " + prefix + lines[0]] +
        ["      " + line for line in lines[1:]]
    )


def _make_items(items, prefix="- ", relationship="and"):
    return [
        _make_item(item, prefix=prefix + relationship + " " if i > 0 else prefix)
            for i, item in enumerate(items)
    ]


def _serialize_sub_matcher_result(matcher, result):
    content = "%s => %s" % (matcher.build_short_description(conjugate=True), "OK" if result.is_success() else "KO")
    if result.description is not None:
        content += ", %s" % result.description
    return content


class AllOf(Matcher):
    def __init__(self, matchers):
        # type: (List[Matcher]) -> None
        self.matchers = matchers

    def build_short_description(self, conjugate=False):
        return ":"

    def build_description(self, conjugate=False):
        return "\n".join(
            [":"] +
            [
                _make_item(matcher.build_description(conjugate=conjugate), prefix="- and " if i > 0 else "- ")
                    for i, matcher in enumerate(self.matchers)
            ]
        )

    def matches(self, actual):
        results = []
        is_success = True
        for matcher in self.matchers:
            result = matcher.matches(actual)
            results.append((matcher, result))
            if result.is_failure():
                is_success = False
                break

        match_details = "\n".join(
            [got() + ":"] +
            _make_items([
                _serialize_sub_matcher_result(matcher, result) for matcher, result in results
            ], relationship="and")
        )

        return match_result(is_success, match_details)


def all_of(*matchers):
    # type: (Any) -> AllOf
    """Test if all matchers match (logical AND between matchers)."""
    return AllOf(list(map(is_, matchers)))


class AnyOf(Matcher):
    def __init__(self, matchers):
        # type: (List[Matcher]) -> None
        self.matchers = matchers

    def build_short_description(self, conjugate=False):
        return ":"

    def build_description(self, conjugate=False):
        return "\n".join(
            [":"] +
            [
                _make_item(matcher.build_description(conjugate=conjugate), prefix="- or " if i > 0 else "- ")
                    for i, matcher in enumerate(self.matchers)
            ]
        )

    def matches(self, actual):
        results = []
        for matcher in self.matchers:
            match = matcher.matches(actual)
            if match.is_success():
                return match
            results.append(match)

        return match_failure(merge_match_result_descriptions(results))


def any_of(*matchers):
    # type: (Any) -> AnyOf
    """Test if at least one of the matcher match (logical OR between matchers)"""
    return AnyOf(list(map(is_, matchers)))


class Anything(Matcher):
    def __init__(self, wording="anything"):
        self.wording = wording

    def build_description(self, conjugate=False):
        return "%s %s" % (to_be(conjugate), self.wording)

    def matches(self, actual):
        return match_success(got_value(actual))


def anything():
    """Matches anything (always succeed, whatever the actual value)"""
    return Anything()


def something():
    """Same thing as the 'anything' matcher but use 'something' in the matcher description"""
    return Anything(wording="something")


def existing():
    """Same thing as the 'anything' matcher but use 'existing' in the matcher description"""
    return Anything(wording="existing")


def present():
    """Same thing as the 'anything' matcher but use 'present' in the matcher description"""
    return Anything(wording="present")


def is_(matcher):
    # type: (Any) -> Matcher
    """If the function argument is not an instance of Matcher, wrap it into
    a matcher using equal_to, otherwise return the matcher argument as-is"""
    from lemoncheesecake.matching.matchers.value import equal_to
    return matcher if isinstance(matcher, Matcher) else equal_to(matcher)


class Not(Matcher):
    def __init__(self, matcher):
        # type: (Matcher) -> None
        self.matcher = matcher

    def build_description(self, conjugate=False):
        return "not %s" % self.matcher.build_description(conjugate)

    def matches(self, actual):
        result = self.matcher.matches(actual)
        return match_result(not result.is_successful, result.description)


def not_(matcher):
    # type: (Any) -> Matcher
    """Negates the matcher in argument"""
    return Not(is_(matcher))
