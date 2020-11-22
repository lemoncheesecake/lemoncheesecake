from callee import Contains, Any

from helpers.matching import assert_match_success, assert_match_failure

from lemoncheesecake.matching.matchers import *


def test_has_item_success():
    result = assert_match_success(has_item(greater_than(2)), [1, 3], Contains("index 1"))
    assert result.index == 1
    assert result.item == 3


def test_has_item_failure():
    result = assert_match_failure(has_item(greater_than(2)), [1, 2], "No matching item")
    assert result.index == -1
    assert result.item is None


def test_has_items_success():
    assert_match_success(has_items([1, 2]), [1, 2, 3], Any())


def test_has_items_failure():
    assert_match_failure(has_items([1, 2]), [1, 3], Contains("Missing") & Contains("2"))


def test_has_only_items_success():
    assert_match_success(has_only_items([3, 1, 2]), [1, 2, 3], Any())


def test_has_only_items_failure_missing():
    assert_match_failure(has_only_items([1, 2, 3]), [1, 3], Contains("Missing") & Contains("2"))


def test_has_only_items_extra_missing():
    assert_match_failure(has_only_items([1, 2, 3]), [4, 1, 2, 3], Contains("Extra") & Contains("4"))


def test_has_all_items_success():
    assert_match_success(has_all_items(greater_than(1)), (2, 3, 4))


def test_has_all_items_failure():
    assert_match_failure(has_all_items(greater_than(1)), (0, 1, 2), Contains("at index 0") & Contains("at index 1"))


def test_is_in_success():
    assert_match_success(is_in([1, 2, 3]), 1, Contains("1"))


def test_is_in_failure():
    assert_match_failure(is_in([1, 2, 3]), 4, Contains("4"))
