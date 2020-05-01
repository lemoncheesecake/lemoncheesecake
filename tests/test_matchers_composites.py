from callee import Contains

from helpers.matching import assert_match_success, assert_match_failure, assert_matcher_description

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


def test_all_of_description_with_two_simple_matchers():
    assert_matcher_description(
        all_of(is_integer(), greater_than(0)),
        Contains("to be an integer and to be greater than 0")
    )


def test_all_of_description_with_any_of_matcher():
    assert_matcher_description(
        all_of(is_integer(), any_of(less_than(10), greater_than(20))),
        Contains("    - to be an integer\n    - and to be less than 10 or to be greater than 20")
    )


def test_all_of_description_with_too_long_description():
    assert_matcher_description(
        all_of(starts_with("A" * 50), ends_with("B" * 50)),
        Contains('    - to start with "%s"\n    - and to end with "%s"' % ("A" * 50, "B" * 50))
    )


def test_any_of_success():
    assert_match_success(any_of(equal_to("foo"), equal_to("bar")), "bar", Contains("bar"))


def test_any_of_failure():
    assert_match_failure(any_of(equal_to("foo"), equal_to("bar")), "baz", Contains("baz"))


def test_any_of_description_with_two_simple_matchers():
    assert_matcher_description(
        any_of(equal_to(1), equal_to(2)),
        Contains("to be equal to 1 or to be equal to 2")
    )


def test_any_of_description_with_all_of_matcher():
    assert_matcher_description(
        any_of(equal_to(1), all_of(greater_than(10), less_than(20))),
        Contains("    - to be equal to 1\n    - or to be greater than 10 and to be less than 20")
    )


def test_any_of_description_with_too_long_description():
    assert_matcher_description(
        any_of(equal_to("A" * 50), equal_to("B" * 50)),
        Contains('    - to be equal to "%s"\n    - or to be equal to "%s"' % ("A" * 50, "B" * 50))
    )


def test_anything():
    assert_match_success(anything(), "foo", Contains("foo"))


def test_something():
    assert_match_success(something(), "foo", Contains("foo"))


def test_existing():
    assert_match_success(existing(), "foo", Contains("foo"))


def test_present():
    assert_match_success(present(), "foo", Contains("foo"))
