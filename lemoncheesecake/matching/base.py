'''
Created on Mar 27, 2017

@author: nicolas
'''

import json

from lemoncheesecake.helpers.orderedset import OrderedSet


class MatchResult(object):
    def __init__(self, is_successful, description):
        self.is_successful = is_successful
        self.description = description

    def __bool__(self):
        return self.is_successful

    def __nonzero__(self):
        return self.__bool__()

    def is_success(self):
        return self.is_successful is True

    def is_failure(self):
        return self.is_successful is False


def match_success(description=None):
    return MatchResult(True, description)


def match_failure(description):
    return MatchResult(False, description)


def match_result(is_successful, description=None):
    return MatchResult(is_successful, description)


class Matcher(object):
    def build_description(self, conjugate=False):
        raise NotImplemented()

    def build_short_description(self, conjugate=False):
        return self.build_description(conjugate=conjugate)

    def matches(self, actual):
        raise NotImplemented()


class MatchExpected(Matcher):
    def __init__(self, expected):
        self.expected = expected


def serialize_value(value):
    return json.dumps(value, ensure_ascii=False)


def serialize_values(values):
    return ", ".join(map(serialize_value, values))


def got(value=None):
    ret = "got"
    if value is not None:
        ret += " " + value
    return ret


def got_value(value):
    return got(serialize_value(value))


def got_values(values):
    return got(serialize_values(values))


def merge_match_result_descriptions(results):
    return ", ".join(
        OrderedSet([result.description for result in results if result.description])
    )


def to_be(conjugate=False, negation=False):
    negative_form = " not" if negation else ""
    return "is%s" % negative_form if conjugate else "to%s be" % negative_form


def to_have(conjugate=False, negation=False):
    negative_form = " not" if negation else ""
    return "has%s" % negative_form if conjugate else "to%s have" % negative_form


def to_meet(conjugate=False, negation=False):
    if conjugate:
        if negation:
            return "does not meet"
        else:
            return "meets"
    else:
        if negation:
            return "to not meet"
        else:
            return "to meet"
