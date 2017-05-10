from lemoncheesecake.matching.matchers import *

def test_is_with_value():
    result = is_(1).matches(1)
    assert result.is_success()
    assert "1" in result.description

def test_is_with_matcher():
    result = is_(greater_than(1)).matches(2)
    assert result.is_success()
    assert "2" in result.description

def test_is_not_success():
    result = is_not(greater_than(1)).matches(1)
    assert result.is_success()
    assert "1" in result.description

def test_is_not_failure():
    result = is_not(greater_than(1)).matches(2)
    assert result.is_failure()
    assert "2" in result.description

def test_all_of_success():
    result = all_of(greater_than(1), less_than(3)).matches(2)
    assert result.is_success()
    assert "2" in result.description

def test_all_of_failure():
    result = all_of(greater_than(1), less_than(3)).matches(3)
    assert result.is_failure()
    assert "3" in result.description

def test_any_of_success():
    result = any_of(equal_to("foo"), equal_to("bar")).matches("bar")
    assert result.is_success()
    assert "bar" in result.description

def test_any_of_failure():
    result = any_of(equal_to("foo"), equal_to("bar")).matches("baz")
    assert result.is_failure()
    assert "baz" in result.description

def test_anything():
    result = anything().matches("foo")
    assert result.is_success()
    assert "foo" in result.description

def test_something():
    result = something().matches("foo")
    assert result.is_success()
    assert "foo" in result.description
    
def test_existing():
    result = existing().matches("foo")
    assert result.is_success()
    assert "foo" in result.description