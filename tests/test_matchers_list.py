from helpers.matching import assert_match_success, assert_match_failure

from lemoncheesecake.matching.matchers import *


def test_has_item_success():
    result = assert_match_success(has_item(greater_than(2)), [1, 3], "index 1")
    assert result.index == 1
    assert result.item == 3


def test_has_item_failure():
    result = assert_match_failure(has_item(greater_than(2)), [1, 2], "no matching")
    assert result.index == -1
    assert result.item is None


def test_has_items_success():
    assert_match_success(has_items([1, 2]), [1, 2, 3], "got")


def test_has_items_failure():
    assert_match_failure(has_items([1, 2]), [1, 3], ["Missing", "2"])


def test_has_only_items_success():
    assert_match_success(has_only_items([3, 1, 2]), [1, 2, 3], "got")


def test_has_only_items_failure_missing():
    assert_match_failure(has_only_items([1, 2, 3]), [1, 3], ["Missing", "2"])


def test_has_only_items_extra_missing():
    assert_match_failure(has_only_items([1, 2, 3]), [4, 1, 2, 3], ["Extra", "4"])


def test_is_in_success():
    assert_match_success(is_in([1, 2, 3]), 1, "1")


def test_is_in_failure():
    assert_match_failure(is_in([1, 2, 3]), 4, "4")
