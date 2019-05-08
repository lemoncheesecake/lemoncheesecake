'''
Created on Apr 1, 2017

@author: nicolas
'''

from lemoncheesecake.matching.base import Matcher, match_failure, match_success, got_value, to_have, serialize_value
from lemoncheesecake.matching.matchers.composites import is_


class EntryMatcher(object):
    def build_description(self):
        raise NotImplemented()

    def get_entry(self, actual):
        """Return the value of dict corresponding to entry matching or raise KeyError if entry is not found"""
        raise NotImplemented()


class KeyPathMatcher(EntryMatcher):
    """Dict lookup through a list of key, each key represent a level of depth of the dict"""
    def __init__(self, path):
        self.path = path

    def build_description(self):
        return " -> ".join(map(serialize_value, self.path))

    def get_entry(self, actual):
        d = actual
        for key in self.path:
            try:
                d = d[key]
            except TypeError:  # if d is not accessible though key, it will raise TypeError
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

    def build_short_description(self, conjugate=False):
        ret = '%s entry %s' % (to_have(conjugate), self.key_matcher.build_description())
        if self.value_matcher:
            ret += " that " + self.value_matcher.build_short_description(conjugate=True)
        return ret

    def build_description(self, conjugate=False):
        ret = '%s entry %s' % (to_have(conjugate), self.key_matcher.build_description())
        if self.value_matcher:
            ret += " that " + self.value_matcher.build_description(conjugate=True)
        return ret

    def matches(self, actual):
        try:
            value = self.key_matcher.get_entry(actual)
        except KeyError:
            return match_failure('No entry %s' % self.key_matcher.build_description())

        if self.value_matcher:
            return self.value_matcher.matches(value)
        else:
            return match_success(got_value(value))


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
