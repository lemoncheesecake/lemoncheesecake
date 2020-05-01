from callee import Contains

from helpers.matching import assert_match_success, assert_match_failure

from lemoncheesecake.matching.matchers import *


def test_is_with_value():
    assert_match_success(is_(1), 1, Contains("1"))


def test_is_with_matcher():
    assert_match_success(is_(greater_than(1)), 2, Contains("2"))


def test_is_not_success():
    assert_match_success(not_(greater_than(1)), 1, Contains("1"))


def test_is_not_failure():
    assert_match_failure(not_(greater_than(1)), 2, Contains("2"))


def test_all_of_success():
    assert_match_success(all_of(greater_than(1), less_than(3)), 2, Contains("2"))


def test_all_of_failure():
    assert_match_failure(all_of(greater_than(1), less_than(3)), 3, Contains("3"))


def test_any_of_success():
    assert_match_success(any_of(equal_to("foo"), equal_to("bar")), "bar", Contains("bar"))


def test_any_of_failure():
    assert_match_failure(any_of(equal_to("foo"), equal_to("bar")), "baz", Contains("baz"))


def test_anything():
    assert_match_success(anything(), "foo", Contains("foo"))


def test_something():
    assert_match_success(something(), "foo", Contains("foo"))


def test_existing():
    assert_match_success(existing(), "foo", Contains("foo"))


def test_present():
    assert_match_success(present(), "foo", Contains("foo"))
