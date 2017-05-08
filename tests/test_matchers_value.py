from lemoncheesecake.matching.matchers import *

def test_equal_to_success():
    result = equal_to(1).matches(1)
    assert result.is_success()
    assert "1" in result.description

def test_equal_to_failure():
    result = equal_to(1).matches(2)
    assert result.is_failure()
    assert "2" in result.description

def test_not_equal_to_success():
    result = not_equal_to(1).matches(2)
    assert result.is_success()
    assert "2" in result.description

def test_not_equal_to_failure():
    result = not_equal_to(1).matches(1)
    assert result.is_failure()
    assert "1" in result.description

def test_greater_than_success():
    result = greater_than(1).matches(2)
    assert result.is_success()
    assert "2" in result.description

def test_greater_than_failure():
    result = greater_than(1).matches(1)
    assert result.is_failure()
    assert "1" in result.description

def test_greater_than_or_equal_to_success():
    result = greater_than_or_equal_to(1).matches(1)
    assert result.is_success()
    assert "1" in result.description

def test_greater_than_or_equal_to_failure():
    result = greater_than_or_equal_to(1).matches(0)
    assert result.is_failure()
    assert "0" in result.description

def test_less_than_success():
    result = less_than(1).matches(0)
    assert result.is_success()
    assert "0" in result.description

def test_less_than_failure():
    result = less_than(1).matches(1)
    assert result.is_failure()
    assert "1" in result.description

def test_less_than_or_equal_to_success():
    result = less_than_or_equal_to(1).matches(1)
    assert result.is_success()
    assert "1" in result.description

def test_less_than_or_equal_to_failure():
    result = less_than_or_equal_to(1).matches(2)
    assert result.is_failure()
    assert "2" in result.description

def test_is_none_success():
    result = is_none().matches(None)
    assert result.is_success()
    assert "null" in result.description

def test_is_none_failure():
    result = is_none().matches("foo")
    assert result.is_failure()
    assert "foo" in result.description

def test_is_not_none_success():
    result = is_not_none().matches("foo")
    assert result.is_success()
    assert "foo" in result.description

def test_is_not_none_failure():
    result = is_not_none().matches(None)
    assert result.is_failure()
    assert "null" in result.description

def test_has_length_success():
    result = has_length(3).matches("foo")
    assert result.is_success()
    assert "3" in result.description

def test_has_length_with_matcher_success():
    result = has_length(greater_than(2)).matches("foo")
    assert result.is_success()
    assert "3" in result.description

def test_has_length_failure():
    result = has_length(3).matches("foobar")
    assert result.is_failure()
    assert "6" in result.description