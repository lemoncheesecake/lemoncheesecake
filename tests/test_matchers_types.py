# -*- coding: utf-8 -*-

from lemoncheesecake.matching.matchers import *

def test_is_dict_success():
    result = is_dict().matches({})
    assert result.is_success()
    assert "{}" in result.description

def test_is_dict_failure():
    result = is_dict(1).matches("foo")
    assert result.is_failure()
    assert "foo" in result.description

def test_is_float_success():
    result = is_float().matches(1.2)
    assert result.is_success()
    assert "1.2" in result.description

def test_is_float_failure():
    result = is_float().matches(1)
    assert result.is_failure()
    assert "1" in result.description

def test_is_integer_success():
    result = is_integer().matches(1)
    assert result.is_success()
    assert "1" in result.description

def test_is_integer_failure():
    result = is_integer().matches(1.2)
    assert result.is_failure()
    assert "1.2" in result.description

def test_is_bool_success():
    result = is_bool().matches(True)
    assert result.is_success()
    assert "true" in result.description

def test_is_bool_failure():
    result = is_bool().matches(1)
    assert result.is_failure()
    assert "1" in result.description

def test_is_list_success():
    result = is_list().matches([])
    assert result.is_success()
    assert "[]" in result.description

def test_is_list_with_tuple_success():
    result = is_list().matches(())
    assert result.is_success()
    assert "[]" in result.description

def test_is_list_failure():
    result = is_list().matches("foo")
    assert result.is_failure()
    assert "foo" in result.description

def test_is_str_success():
    result = is_str().matches("foo")
    assert result.is_success()
    assert "foo" in result.description

def test_is_str_with_unicode_success():
    result = is_str().matches(u"ààà")
    assert result.is_success()
    assert u"ààà" in result.description

def test_is_str_failure():
    result = is_str().matches(1)
    assert result.is_failure()
    assert "1" in result.description
