'''
Created on Apr 1, 2017

@author: nicolas
'''

from typing import Sequence, Any

from lemoncheesecake.helpers.text import jsonify
from lemoncheesecake.matching.matcher import Matcher, MatchResult, MatcherDescriptionTransformer
from lemoncheesecake.matching.matchers.composites import is_


class EntryMatcher(object):
    def build_description(self):
        raise NotImplementedError()

    def get_entry(self, actual):
        # type: (dict) -> Any
        """Return the value of dict corresponding to entry matching or raise KeyError if entry is not found"""
        raise NotImplementedError()


class KeyPathMatcher(EntryMatcher):
    """Dict lookup through a list of key, each key represent a level of depth of the dict"""
    def __init__(self, path):
        # type: (Sequence[str]) -> None
        self.path = path

    def build_description(self):
        return " -> ".join(map(jsonify, self.path))

    def get_entry(self, actual):
        d = actual
        for key in self.path:
            try:
                d = d[key]
            # make sure to always raise a KeyError even if d is a list/tuple or something
            # that does not support __getitem__
            except (TypeError, IndexError):
                raise KeyError()
        return d


def wrap_key_matcher(key_matcher, base_key=()):
    if isinstance(key_matcher, EntryMatcher):
        return key_matcher
    if type(key_matcher) not in (list, tuple):
        key_matcher = (key_matcher,)
    return KeyPathMatcher(tuple(base_key) + tuple(key_matcher))


class HasEntry(Matcher):
    def __init__(self, key_matcher, value_matcher):
        # type: (EntryMatcher, Matcher) -> None
        self.key_matcher = key_matcher
        self.value_matcher = value_matcher

    def build_short_description(self, transformation):
        ret = transformation('to have entry %s' % self.key_matcher.build_description())
        if self.value_matcher:
            ret += " that " + self.value_matcher.build_short_description(MatcherDescriptionTransformer(conjugate=True))
        return ret

    def build_description(self, transformation):
        ret = transformation('to have entry %s' % self.key_matcher.build_description())
        if self.value_matcher:
            ret += " that " + self.value_matcher.build_description(MatcherDescriptionTransformer(conjugate=True))
        return ret

    def matches(self, actual):
        try:
            value = self.key_matcher.get_entry(actual)
        except KeyError:
            return MatchResult.failure('No entry %s' % self.key_matcher.build_description())

        if self.value_matcher:
            return self.value_matcher.matches(value)
        else:
            return MatchResult.success("got %s" % jsonify(value))


def has_entry(key_matcher, value_matcher=None):
    """
    Test if dict has a <key> entry whose value matches (optional) value_matcher.
    Key entry can a standard dict key or a list of key where each element represent a
    level of depth of the dict (when dict are imbricated)
    """
    return HasEntry(
        wrap_key_matcher(key_matcher),
        is_(value_matcher) if value_matcher is not None else None
    )
