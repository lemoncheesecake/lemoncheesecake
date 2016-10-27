'''
Created on Sep 30, 2016

@author: nicolas
'''

import pytest

import lemoncheesecake as lcc
from lemoncheesecake.exceptions import ProgrammingError

def test_decorator_test():
    class MySuite(lcc.TestSuite):
        @lcc.test("test_desc")
        def mytest(self):
            pass
    suite = MySuite()
    suite.load()
    test = suite.get_tests()[0]
    assert test.id == "mytest"
    assert test.description == "test_desc"

def test_decorator_tags():
    @lcc.tags("tag3")
    class MySuite(lcc.TestSuite):
        @lcc.tags("tag1", "tag2")
        @lcc.test("test_desc")
        def mytest(self):
            pass
    suite = MySuite()
    suite.load()
    assert suite.tags == ["tag3"]
    test = suite.get_tests()[0]
    assert test.tags == ["tag1", "tag2"]

def test_decorator_prop():
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

def test_decorator_link():
    @lcc.link("http://www.example.com", "example")
    class MySuite(lcc.TestSuite):
        @lcc.link("http://www.example.com")
        @lcc.test("test_desc")
        def mytest(self):
            pass
    suite = MySuite()
    suite.load()
    assert suite.links[0] == ("http://www.example.com", "example")
    test = suite.get_tests()[0]
    assert test.links[0] == ("http://www.example.com", None)

def test_decorator_on_invalid_object():
    with pytest.raises(ProgrammingError):
        @lcc.tags("tag")
        class NotATestSuite:
            pass

def test_decorator_with_testsuite_inheritance():
    @lcc.link("http://www.example1.com")
    @lcc.tags("tag1", "tag2")
    @lcc.prop("key1", "value1")
    class MySuite1(lcc.TestSuite):
        pass
    
    @lcc.link("http://www.example2.com")
    @lcc.tags("tag3")
    @lcc.prop("key2", "value2")
    class MySuite2(MySuite1):
        pass
    
    suite1 = MySuite1()
    suite1.load()
    suite2 = MySuite2()
    suite2.load()
    
    assert len(suite1.links) == 1
    assert suite1.links[0] == ("http://www.example1.com", None)
    assert suite1.tags == ["tag1", "tag2"]
    assert len(suite1.properties) == 1
    assert suite1.properties["key1"] == "value1"
    
    assert len(suite2.links) == 2
    assert suite2.links[0] == ("http://www.example1.com", None)
    assert suite2.links[1] == ("http://www.example2.com", None)
    assert suite2.tags == ["tag1", "tag2", "tag3"]
    assert len(suite2.properties) == 2
    assert suite2.properties["key1"] == "value1"
    assert suite2.properties["key2"] == "value2"
    
