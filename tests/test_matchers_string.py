# -*- coding: utf-8 -*-

import re

from callee import Contains, Not

from helpers.matching import assert_match_success, assert_match_failure, assert_matcher_description

from lemoncheesecake.matching.matchers import *
from lemoncheesecake.matching.matchers.string import make_pattern_matcher


def test_starts_with_success():
    assert_match_success(starts_with("foo"), "foobar", Contains("foo"))


def test_starts_with_failure():
    assert_match_failure(starts_with("foo"), "bar", Contains("bar"))


def test_starts_with_failure_not_a_string():
    assert_match_failure(starts_with("foo"), None, Contains("null"))


def test_ends_with_success():
    assert_match_success(ends_with("bar"), "foobar", Contains("foobar"))


def test_ends_with_failure():
    assert_match_failure(ends_with("foo"), "bar", Contains("bar"))


def test_ends_with_failure_not_a_string():
    assert_match_failure(ends_with("foo"), None, Contains("null"))


def test_contains_string_with_success():
    assert_match_success(contains_string("ob"), "foobar", Contains("foobar"))


def test_contains_string_with_failure():
    assert_match_failure(contains_string("ob"), "baz", Contains("baz"))


def test_contains_string_with_failure_not_a_string():
    assert_match_failure(contains_string("ob"), None, Contains("null"))


def test_match_pattern_success():
    assert_match_success(match_pattern("^f"), "foo", Contains("foo"))


def test_match_pattern_search_success():
    # ensure that the `search` method (and not the `match` method) of `re` module is called
    assert_match_success(match_pattern("oo"), "foo", Contains("foo"))


def test_match_pattern_with_pattern_success():
    assert_match_success(match_pattern(re.compile(r"^foo", re.IGNORECASE)), "FOOBAR", Contains("FOOBAR"))


def test_match_pattern_description_default():
    assert_matcher_description(match_pattern(r"^\d+$"), Contains(r"^\d+$"))


def test_match_pattern_description_description():
    assert_matcher_description(
        match_pattern(r"^\d+$", "a number"),
        Contains("a number") & Not(Contains(r"^\d+$"))
    )


def test_match_pattern_description_description_and_mention_regexp():
    assert_matcher_description(
        match_pattern(r"^\d+$", "a number", mention_regexp=True),
        Contains("a number") & Contains(r"^\d+$")
    )


def test_make_pattern_matcher():
    matcher = make_pattern_matcher(r"^\d+$", "a number", mention_regexp=True)
    assert_matcher_description(matcher(), Contains("a number") & Contains(r"^\d+$"))
    assert_match_success(matcher(), "42", Contains("42"))


def test_match_pattern_failure():
    assert_match_failure(match_pattern(r"^f"), "bar", Contains("bar"))


def test_match_pattern_failure_invalid_type():
    assert_match_failure(match_pattern(r"^f"), None, Contains("Invalid value"))


def test_is_text_success():
    assert_match_success(is_text("foo\nbar", "\n"), "foo\nbar")


def test_is_text_failure():
    assert_match_failure(is_text("foo\nbar", "\n"), "foo\nbar\nbaz", Contains("+baz"))


def test_is_json_success():
    assert_match_success(is_json({"foo": 1, "bar": 2}), {"foo": 1, "bar": 2})


def test_is_json_failure():
    assert_match_failure(is_json({"foo": 1, "bar": 2}), {"foo": 1, "bar": 2, "baz": 3}, Contains('+    "baz": 3'))
