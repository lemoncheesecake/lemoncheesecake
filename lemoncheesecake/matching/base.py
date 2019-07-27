'''
Created on Mar 27, 2017

@author: nicolas
'''

import json
import re

from lemoncheesecake.helpers.orderedset import OrderedSet


CONJUGATION_FORMS = {
    re.compile(r"^(to be)"): ("is", "is not", "to not be"),
    re.compile(r"^(to have)"): ("has", "has not", "to have no"),
    re.compile(r"^(to match)"): ("matches", "does not match", "to not match"),
    re.compile(r"^(can)"): ("can", "cannot", "to cannot")
}


class VerbTransformation(object):
    def __init__(self, conjugate=False, negative=False):
        self.conjugate = conjugate
        self.negative = negative

    def __call__(self, sentence):
        ###
        # No transformation to do
        ###
        if not self.conjugate and not self.negative:
            return sentence

        ###
        # Transformation of irregular verb
        ###
        for pattern, forms in CONJUGATION_FORMS.items():
            conjugated, conjugated_negative, infinitive_negative = forms
            if self.conjugate and self.negative:
                substitution = conjugated_negative
            elif self.conjugate:
                substitution = conjugated
            else:  # self.negative
                substitution = infinitive_negative

            if pattern.match(sentence):
                return pattern.sub(substitution, sentence)

        ###
        # Transformation of regular verb
        ###
        pattern = re.compile(r"^to (\w+)")
        m = pattern.match(sentence)
        if m:
            if self.conjugate and self.negative:
                substitution = "does not " + m.group(1)
            elif self.conjugate:
                substitution = m.group(1) + "s"
            elif self.negative:
                substitution = "to not " + m.group(1)
            else:
                substitution = "not " + m.group(1)

            return pattern.sub(substitution, sentence)

        ###
        # No verb detected
        ###
        return sentence


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
    def build_description(self, transformation):
        raise NotImplemented()

    def build_short_description(self, transformation):
        return self.build_description(transformation)

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
