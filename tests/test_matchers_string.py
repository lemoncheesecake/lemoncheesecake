# -*- coding: utf-8 -*-

import re

from lemoncheesecake.matching.matchers import *

def test_starts_with_success():
    result = starts_with("foo").matches("foobar")
    assert result.is_success()
    assert "foobar" in result.description

def test_starts_with_failure():
    result = starts_with("foo").matches("bar")
    assert result.is_failure()
    assert "bar" in result.description

def test_ends_with_success():
    result = ends_with("bar").matches("foobar")
    assert result.is_success()
    assert "foobar" in result.description

def test_ends_with_failure():
    result = ends_with("foo").matches("bar")
    assert result.is_failure()
    assert "bar" in result.description

def test_match_pattern_success():
    result = match_pattern("^f").matches("foo")
    assert result.is_success()
    assert "foo" in result.description

def test_match_pattern_with_pattern_success():
    result = match_pattern(re.compile("^foo", re.IGNORECASE)).matches("FOOBAR")
    assert result.is_success()
    assert "FOOBAR" in result.description

def test_match_pattern_failure():
    result = match_pattern("^f").matches("bar")
    assert result.is_failure()
    assert "bar" in result.description
