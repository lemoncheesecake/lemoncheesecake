from helpers import assert_match_success, assert_match_failure

from lemoncheesecake.matching.matchers import *

def test_has_item_success():
    assert_match_success(has_item(greater_than(2)), [1, 3], "3")

def test_has_item_failure():
    assert_match_failure(has_item(greater_than(2)), [1, 2], "No matching")

def test_has_values_success():
    assert_match_success(has_values([1, 2]), [1, 2, 3], "Got")

def test_has_values_failure():
    assert_match_failure(has_values([1, 2]), [1, 3], ["Missing", "2"])

def test_has_only_values_success():
    assert_match_success(has_only_values([3, 1, 2]), [1, 2, 3], "Got")

def test_has_only_values_failure_missing():
    assert_match_failure(has_only_values([1, 2, 3]), [1, 3], ["Missing", "2"])

def test_has_only_values_extra_missing():
    assert_match_failure(has_only_values([1, 2, 3]), [4, 1, 2, 3], ["Extra", "4"])

def test_is_in_success():
    assert_match_success(is_in([1, 2, 3]), 1, "1")

def test_is_in_failure():
    assert_match_failure(is_in([1, 2, 3]), 4, "4")
