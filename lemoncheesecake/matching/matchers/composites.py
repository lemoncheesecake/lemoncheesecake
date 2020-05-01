'''
Created on Mar 28, 2017

@author: nicolas
'''

from typing import List, Any

from lemoncheesecake.helpers.orderedset import OrderedSet
from lemoncheesecake.helpers.text import jsonify
from lemoncheesecake.matching.matcher import Matcher, MatchResult, MatcherDescriptionTransformer


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


def _build_multi_line_description(matchers, transformation, relationship):
    return "\n".join(
        [":"] +
        [
            _make_item(matcher.build_description(transformation), prefix="- %s " % relationship if i > 0 else "- ")
                for i, matcher in enumerate(matchers)
        ]
    )


def _build_single_line_description_if_suitable(matchers, transformation, relationship):
    if any(isinstance(matcher, (AllOf, AnyOf)) for matcher in matchers):
        # in case of "composite of composite", the multi-line rendering must be used in order to keep the logic
        return None

    descriptions = [matcher.build_description(transformation) for matcher in matchers]
    if any("\n" in desc for desc in descriptions):
        # in case of a \n in a matcher description, the resulting description will not be readable
        return None

    description = " {} ".format(relationship).join(descriptions)
    if len(description) > 100:
        # if the resulting description is more than 100 characters, we probably better keep multi-line rendering
        return None

    return description


def _build_composite_description(matchers, transformation, relationship):
    description = _build_single_line_description_if_suitable(matchers, transformation, relationship)
    if description:
        return description
    else:
        return _build_multi_line_description(matchers, transformation, relationship)


def _serialize_sub_matcher_result(matcher, result):
    content = "%s => %s" % (matcher.build_short_description(MatcherDescriptionTransformer()), "OK" if result else "KO")
    if result.description is not None:
        content += ", %s" % result.description
    return content


class AllOf(Matcher):
    def __init__(self, matchers):
        # type: (List[Matcher]) -> None
        self.matchers = matchers

    def build_short_description(self, transformation):
        return ":"

    def build_description(self, transformation):
        return _build_composite_description(self.matchers, transformation, "and")

    def matches(self, actual):
        results = []
        is_success = True
        for matcher in self.matchers:
            result = matcher.matches(actual)
            results.append((matcher, result))
            if not result:
                is_success = False
                break

        match_details = "\n".join(
            ["got:"] +
            _make_items([
                _serialize_sub_matcher_result(matcher, result) for matcher, result in results
            ], relationship="and")
        )

        return MatchResult(is_success, match_details)


def all_of(*matchers):
    # type: (Any) -> AllOf
    """Test if all matchers match (logical AND between matchers)."""
    return AllOf(list(map(is_, matchers)))


class AnyOf(Matcher):
    def __init__(self, matchers):
        # type: (List[Matcher]) -> None
        self.matchers = matchers

    def build_short_description(self, transformation):
        return ":"

    def build_description(self, transformation):
        return _build_composite_description(self.matchers, transformation, "or")

    def matches(self, actual):
        results = []
        for matcher in self.matchers:
            match = matcher.matches(actual)
            if match:
                return match
            results.append(match)

        return MatchResult.failure(
            ", ".join(
                OrderedSet(result.description for result in results if result.description)
            )
        )


def any_of(*matchers):
    # type: (Any) -> AnyOf
    """Test if at least one of the matcher match (logical OR between matchers)"""
    return AnyOf(list(map(is_, matchers)))


class Anything(Matcher):
    def __init__(self, wording="to be anything"):
        self.wording = wording

    def build_description(self, transformation):
        return transformation(self.wording)

    def matches(self, actual):
        return MatchResult.success("got %s" % jsonify(actual))


def anything():
    """Matches anything (always succeed, whatever the actual value)"""
    return Anything()


def something():
    """Same thing as the 'anything' matcher but use 'to be something' in the matcher description"""
    return Anything(wording="to be something")


def existing():
    """Same thing as the 'anything' matcher but use 'to exist' in the matcher description"""
    return Anything(wording="to exist")


def present():
    """Same thing as the 'anything' matcher but use 'to be present' in the matcher description"""
    return Anything(wording="to be present")


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

    def build_description(self, transformation):
        transformation.negative = True
        return self.matcher.build_description(transformation)

    def matches(self, actual):
        result = self.matcher.matches(actual)
        return MatchResult(not result, result.description)


def not_(matcher):
    # type: (Any) -> Matcher
    """Negates the matcher in argument"""
    return Not(is_(matcher))


is_not = not_
