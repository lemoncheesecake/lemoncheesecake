# -*- coding: utf-8 -*-

from helpers import assert_match_success, assert_match_failure

from lemoncheesecake.matching.matchers import *

def test_has_entry_success():
    assert_match_success(has_entry("foo"), {"foo": "bar"}, "bar")

def test_has_entry_with_matcher_success():
    assert_match_success(has_entry("foo", equal_to("bar")), {"foo": "bar"}, "bar")

def test_has_entry_failure():
    assert_match_failure(has_entry("foo"), {}, "No entry")

def test_has_entry_with_matcher_failure():
    assert_match_failure(has_entry("foo", equal_to("bar")), {"foo": "baz"}, "baz")

def test_has_entry_using_list_success():
    assert_match_success(has_entry(["foo", "bar"]), {"foo": {"bar": "baz"}}, "baz")

def test_has_entry_using_list_failure():
    assert_match_failure(has_entry(["foo", "bar"]), {"foo": "baz"}, "No entry")
