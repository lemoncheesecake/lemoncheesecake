'''
Created on Sep 30, 2016

@author: nicolas
'''

import pytest

import lemoncheesecake as lcc
from lemoncheesecake.exceptions import ProgrammingError

def test_testsuite_decorator_test():
    class MySuite(lcc.TestSuite):
        @lcc.test("test_desc")
        def mytest(self):
            pass
    suite = MySuite()
    suite.load()
    test = suite.get_tests()[0]
    assert test.id == "mytest"
    assert test.description == "test_desc"

def test_testsuite_decorator_tags():
    @lcc.tags("tag3")
    class MySuite(lcc.TestSuite):
        @lcc.tags("tag1", "tag2")
        @lcc.test("test_desc")
        def mytest(self):
            pass
    suite = MySuite()
    suite.load()
    assert suite.tags == ("tag3",)
    test = suite.get_tests()[0]
    assert test.tags == ("tag1", "tag2")

def test_testsuite_decorator_prop():
    @lcc.prop("key1", "val1")
    class MySuite(lcc.TestSuite):
        @lcc.prop("key2", "val2")
        @lcc.test("test_desc")
        def mytest(self):
            pass
    suite = MySuite()
    suite.load()
    assert suite.properties["key1"] == "val1"
    test = suite.get_tests()[0]
    assert test.properties["key2"] == "val2"

def test_testsuite_decorator_url():
    @lcc.url("http://www.example.com", "example")
    class MySuite(lcc.TestSuite):
        @lcc.url("http://www.example.com")
        @lcc.test("test_desc")
        def mytest(self):
            pass
    suite = MySuite()
    suite.load()
    assert suite.urls[0] == ("http://www.example.com", "example")
    test = suite.get_tests()[0]
    assert test.urls[0] == ("http://www.example.com", None)

def test_testsuite_decorator_on_invalid_object():
    with pytest.raises(ProgrammingError):
        @lcc.tags("tag")
        class NotATestSuite:
            pass