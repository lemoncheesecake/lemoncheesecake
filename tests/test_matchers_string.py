# -*- coding: utf-8 -*-

import re

from helpers import assert_match_success, assert_match_failure

from lemoncheesecake.matching.matchers import *

def test_starts_with_success():
    assert_match_success(starts_with("foo"), "foobar", "foo")

def test_starts_with_failure():
    assert_match_failure(starts_with("foo"), "bar", "bar")

def test_ends_with_success():
    assert_match_success(ends_with("bar"), "foobar", "foobar")

def test_ends_with_failure():
    assert_match_failure(ends_with("foo"), "bar", "bar")

def test_contains_string_with_success():
    assert_match_success(contains_string("ob"), "foobar", "foobar")

def test_contains_string_with_failure():
    assert_match_failure(contains_string("ob"), "baz", "baz")

def test_match_pattern_success():
    assert_match_success(match_pattern("^f"), "foo", "foo")

def test_match_pattern_search_success():
    # ensure that the `search` method (and not the `match` method) of `re` module is called
    assert_match_success(match_pattern("oo"), "foo", "foo")

def test_match_pattern_with_pattern_success():
    assert_match_success(match_pattern(re.compile("^foo", re.IGNORECASE)), "FOOBAR", "FOOBAR")

def test_match_pattern_failure():
    assert_match_failure(match_pattern("^f"), "bar", "bar")
