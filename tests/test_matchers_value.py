from callee import Contains

from helpers.runner import run_func_in_test
from helpers.matching import assert_match_success, assert_match_failure
from helpers.report import get_last_logged_check

from lemoncheesecake.matching.matchers import *
from lemoncheesecake.matching import check_that


def test_equal_to_success():
    assert_match_success(equal_to(1), 1, Contains("1"))


def test_equal_to_success_with_details():
    from lemoncheesecake import matching
    matching.DISPLAY_DETAILS_WHEN_EQUAL = False

    try:
        check = get_last_logged_check(run_func_in_test(lambda: check_that("value", 1, equal_to(1))))
        assert check.is_successful is True
        assert check.details is None
    finally:
        matching.DISPLAY_DETAILS_WHEN_EQUAL = True


def test_equal_to_failure():
    assert_match_failure(equal_to(1), 2, Contains("2"))


def test_not_equal_to_success():
    assert_match_success(not_equal_to(1), 2, Contains("2"))


def test_not_equal_to_failure():
    assert_match_failure(not_equal_to(1), 1, Contains("1"))


def test_greater_than_success():
    assert_match_success(greater_than(1), 2, Contains("2"))


def test_greater_than_failure():
    assert_match_failure(greater_than(1), 1, Contains("1"))


def test_greater_than_or_equal_to_success():
    assert_match_success(greater_than_or_equal_to(1), 1, Contains("1"))


def test_greater_than_or_equal_to_failure():
    assert_match_failure(greater_than_or_equal_to(1), 0, Contains("0"))


def test_less_than_success():
    assert_match_success(less_than(1), 0, Contains("0"))


def test_less_than_failure():
    assert_match_failure(less_than(1), 1, Contains("1"))


def test_less_than_or_equal_to_success():
    assert_match_success(less_than_or_equal_to(1), 1, Contains("1"))


def test_less_than_or_equal_to_failure():
    assert_match_failure(less_than_or_equal_to(1), 2, Contains("2"))


def test_is_between_success():
    assert_match_success(is_between(1, 3), 2, Contains("2"))


def test_is_between_failure():
    assert_match_failure(is_between(1, 3), 4, Contains("4"))


def test_is_none_success():
    assert_match_success(is_none(), None, Contains("null"))


def test_is_none_failure():
    assert_match_failure(is_none(), "foo", Contains("foo"))


def test_is_not_none_success():
    assert_match_success(is_not_none(), "foo", Contains("foo"))


def test_is_not_none_failure():
    assert_match_failure(is_not_none(), None, Contains("null"))


def test_has_length_success():
    assert_match_success(has_length(3), "foo", Contains("3"))


def test_has_length_with_matcher_success():
    assert_match_success(has_length(greater_than(2)), "foo", Contains("3"))


def test_has_length_failure():
    assert_match_failure(has_length(3), "foobar", Contains("6"))


def test_is_true_success():
    assert_match_success(is_true(), True, Contains("true"))


def test_is_true_failure_wrong_value():
    assert_match_failure(is_true(), False, Contains("false"))


def test_is_true_failure_wrong_type():
    assert_match_failure(is_true(), 1, Contains("1"))


def test_is_false_success():
    assert_match_success(is_false(), False, Contains("false"))


def test_is_false_failure_wrong_value():
    assert_match_failure(is_false(), True, Contains("true"))


def test_is_false_failure_wrong_type():
    assert_match_failure(is_false(), 0, Contains("0"))
