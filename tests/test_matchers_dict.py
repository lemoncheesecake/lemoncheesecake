# -*- coding: utf-8 -*-

from callee import Contains

from helpers.matching import assert_match_success, assert_match_failure

from lemoncheesecake.matching.matchers import *


def test_has_entry_success():
    assert_match_success(has_entry("foo"), {"foo": "bar"}, Contains("bar"))


def test_has_entry_with_matcher_success():
    assert_match_success(has_entry("foo", equal_to("bar")), {"foo": "bar"}, Contains("bar"))


def test_has_entry_failure():
    assert_match_failure(has_entry("foo"), {}, Contains("No entry"))


def test_has_entry_with_matcher_failure():
    assert_match_failure(has_entry("foo", equal_to("bar")), {"foo": "baz"}, Contains("baz"))


def test_has_entry_using_list_success():
    assert_match_success(has_entry(["foo", "bar"]), {"foo": {"bar": "baz"}}, Contains("baz"))


def test_has_entry_using_list_failure():
    assert_match_failure(has_entry(["foo", "bar"]), {"foo": "baz"}, Contains("No entry"))


def test_has_entry_using_list_index_success():
    assert_match_success(has_entry(("foo", 0)), {"foo": ["bar"]})


def test_has_entry_using_list_index_failure():
    assert_match_failure(has_entry(("foo", 0)), {"foo": []}, Contains("No entry"))
