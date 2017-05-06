from lemoncheesecake.matching.matchers import *

def test_has_item_success():
    result = has_item(greater_than(2)).matches([1, 3])
    assert result.is_success()
    assert "3" in result.description

def test_has_item_failure():
    result = has_item(greater_than(2)).matches([1, 2])
    assert result.is_failure()
    assert "No matching" in result.description

def test_has_values_success():
    result = has_values([1, 2]).matches([1, 2, 3])
    assert result.is_success()
    assert "Got" in result.description

def test_has_values_failure():
    result = has_values([1, 2]).matches([1, 3])
    assert result.is_failure()
    assert "Missing" in result.description and "2" in result.description

def test_has_only_values_success():
    result = has_only_values([3, 1, 2]).matches([1, 2, 3])
    assert result.is_success()
    assert "Got" in result.description

def test_has_only_values_failure_missing():
    result = has_only_values([1, 2, 3]).matches([1, 3])
    assert result.is_failure()
    assert "Missing" in result.description and "2" in result.description

def test_has_only_values_extra_missing():
    result = has_only_values([1, 2, 3]).matches([4, 1, 2, 3])
    assert result.is_failure()
    assert "Extra" in result.description and "4" in result.description
