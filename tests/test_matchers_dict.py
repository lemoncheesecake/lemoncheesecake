# -*- coding: utf-8 -*-

from lemoncheesecake.matching.matchers import *

def test_has_entry_success():
    result = has_entry("foo").matches({"foo": "bar"})
    assert result.is_success()
    assert "bar" in result.description

def test_has_entry_with_matcher_success():
    result = has_entry("foo", equal_to("bar")).matches({"foo": "bar"})
    assert result.is_success()
    assert "bar" in result.description

def test_has_entry_failure():
    result = has_entry("foo").matches({})
    assert result.is_failure()
    assert "No entry" in result.description

def test_has_entry_with_matcher_failure():
    result = has_entry("foo", equal_to("bar")).matches({"foo": "baz"})
    assert result.is_failure()
    assert "baz" in result.description
