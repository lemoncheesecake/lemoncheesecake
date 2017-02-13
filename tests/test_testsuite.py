 # -*- coding: utf-8 -*-

'''
Created on Sep 30, 2016

@author: nicolas
'''

import pytest

import lemoncheesecake as lcc
from lemoncheesecake.exceptions import ProgrammingError, InvalidMetadataError

from helpers import dummy_test_callback

def test_decorator_test():
    class MySuite(lcc.TestSuite):
        @lcc.test("test_desc")
        def mytest(self):
            pass
    suite = MySuite()
    suite.load()
    test = suite.get_tests()[0]
    assert test.name == "mytest"
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

def test_decorator_unicode():
    @lcc.link("http://foo.bar", u"éééààà")
    @lcc.prop(u"ééé", u"ààà")
    @lcc.tags(u"ééé", u"ààà")
    class MySuite(lcc.TestSuite):
        @lcc.link("http://foo.bar", u"éééààà")
        @lcc.prop(u"ééé", u"ààà")
        @lcc.tags(u"ééé", u"ààà")
        @lcc.test(u"Some test ààà")
        def sometest(self):
            pass
    
    suite = MySuite()
    suite.load()
    
    assert suite.links[0] == ("http://foo.bar", u"éééààà")
    assert suite.properties[u"ééé"] == u"ààà"
    assert suite.tags == [u"ééé", u"ààà"]
    
    test = suite.get_tests()[0]
    assert test.description == u"Some test ààà"
    assert test.links[0] == ("http://foo.bar", u"éééààà")
    assert test.properties[u"ééé"] == u"ààà"
    assert test.tags == [u"ééé", u"ààà"]

def test_duplicated_suite_description():
    class MySuite(lcc.TestSuite):
        class SubSuite1(lcc.TestSuite):
            description = "somedesc"
        class SubSuite2(lcc.TestSuite):
            description = "somedesc"
    
    suite = MySuite()
    with pytest.raises(InvalidMetadataError) as excinfo:
        suite.load()

def test_duplicated_test_description():
    class MySuite(lcc.TestSuite):
        @lcc.test("somedesc")
        def foo(self):
            pass
        
        @lcc.test("somedesc")
        def bar(self):
            pass
    
    suite = MySuite()
    with pytest.raises(InvalidMetadataError) as excinfo:
        suite.load()

def test_duplicated_test_name():
    class MySuite(lcc.TestSuite):
        def load_generated_tests(self):
            self.register_test(lcc.Test("mytest", "First test", dummy_test_callback))
            self.register_test(lcc.Test("mytest", "Second test", dummy_test_callback))
            
    suite = MySuite()
    with pytest.raises(InvalidMetadataError) as excinfo:
        suite.load()

def test_register_test():
    class MySuite(lcc.TestSuite):
        def load_generated_tests(self):
            self.register_test(lcc.Test("mytest", "My Test", dummy_test_callback))
    
    suite = MySuite()
    suite.load()
    assert len(suite.get_tests()) == 1

def test_register_test_multiple():
    class MySuite(lcc.TestSuite):
        def load_generated_tests(self):
            for i in range(3):
                self.register_test(lcc.Test("mytest_%d" % i, "My Test %d" % i, dummy_test_callback))
    
    suite = MySuite()
    suite.load()
    assert len(suite.get_tests()) == 3

def test_register_tests():
    class MySuite(lcc.TestSuite):
        def load_generated_tests(self):
            tests = [lcc.Test("mytest_%d" % i, "My Test %d" % i, dummy_test_callback) for i in range(3)]
            self.register_tests(tests)
    
    suite = MySuite()
    suite.load()
    assert len(suite.get_tests()) == 3

def test_register_test_with_before_and_after():
    class MySuite(lcc.TestSuite):
        @lcc.test("Bar 1")
        def bar1(self):
            pass
        
        @lcc.test("Bar 2")
        def bar2(self):
            pass
        
        def load_generated_tests(self):
            self.register_test(lcc.Test("foo1", "Foo 1", dummy_test_callback), before_test="bar1")
            self.register_test(lcc.Test("foo2", "Foo 2", dummy_test_callback), before_test="bar1")
            self.register_test(lcc.Test("baz1", "Baz 1", dummy_test_callback), after_test="bar2")
            self.register_test(lcc.Test("baz2", "Baz 2", dummy_test_callback), after_test="baz1")
    
    suite = MySuite()
    suite.load()
    
    assert [t.name for t in suite.get_tests()] == ["foo1", "foo2", "bar1", "bar2", "baz1", "baz2"]

def test_register_tests_with_before_and_after():
    class MySuite(lcc.TestSuite):
        @lcc.test("Bar 1")
        def bar1(self):
            pass
        
        @lcc.test("Bar 2")
        def bar2(self):
            pass
        
        def load_generated_tests(self):
            self.register_tests(
                [lcc.Test("foo1", "Foo 1", dummy_test_callback), lcc.Test("foo2", "Foo 2", dummy_test_callback)],
                before_test="bar1"
            )
            self.register_tests(
                [lcc.Test("baz1", "Baz 1", dummy_test_callback), lcc.Test("baz2", "Baz 2", dummy_test_callback)],
                after_test="bar2"
            )
    
    suite = MySuite()
    suite.load()
    
    assert [t.name for t in suite.get_tests()] == ["foo1", "foo2", "bar1", "bar2", "baz1", "baz2"]

def test_get_fixtures():
    class MySuite(lcc.TestSuite):
        @lcc.test("Test 1")
        def test_1(self, foo):
            pass
        
        class MySubSuite(lcc.TestSuite):
            @lcc.test("Test 2")
            def test_2(self, bar, baz):
                pass

            @lcc.test("Test 3")
            def test_3(self, baz):
                pass

            @lcc.test("Test 4")
            def test_4(self):
                pass

    suite = MySuite()
    suite.load()
    
    assert suite.get_fixtures() == ["foo", "bar", "baz"]

def test_get_fixtures_non_recursive():
    class MySuite(lcc.TestSuite):
        @lcc.test("Test 1")
        def test_1(self, foo):
            pass
        
        class MySubSuite(lcc.TestSuite):
            @lcc.test("Test 2")
            def test_2(self, bar, baz):
                pass

            @lcc.test("Test 3")
            def test_3(self, baz):
                pass

            @lcc.test("Test 4")
            def test_4(self):
                pass

    suite = MySuite()
    suite.load()
    
    assert suite.get_fixtures(recursive=False) == ["foo"]

def test_get_inherited_test_tags():
    @lcc.tags("tag1")
    class MySuite(lcc.TestSuite):
        class MySubSuite(lcc.TestSuite):
            @lcc.tags("tag2")
            @lcc.test("Test 2")
            def test(self):
                pass
    
    suite = MySuite()
    suite.load()
    
    assert suite.get_sub_testsuites()[0].get_inherited_test_tags(suite.get_sub_testsuites()[0].get_tests()[0]) \
        == ["tag1", "tag2"]

def test_get_inherited_test_properties():
    @lcc.prop("prop1", "foo")
    @lcc.prop("prop2", "bar")
    class MySuite(lcc.TestSuite):
        @lcc.prop("prop3", "foobar")
        class MySubSuite(lcc.TestSuite):
            @lcc.prop("prop1", "baz")
            @lcc.test("Test 2")
            def test(self):
                pass
    
    suite = MySuite()
    suite.load()
    
    assert suite.get_sub_testsuites()[0].get_inherited_test_properties(suite.get_sub_testsuites()[0].get_tests()[0]) \
        == {"prop1": "baz", "prop2": "bar", "prop3": "foobar"}

def test_get_inherited_test_links():
    @lcc.link("http://www.example.com/1234")
    class MySuite(lcc.TestSuite):
        class MySubSuite(lcc.TestSuite):
            @lcc.link("http://www.example.com/1235", "#1235")
            @lcc.test("Test 2")
            def test(self):
                pass
    
    suite = MySuite()
    suite.load()
    
    assert suite.get_sub_testsuites()[0].get_inherited_test_links(suite.get_sub_testsuites()[0].get_tests()[0]) \
        == [("http://www.example.com/1234", None), ("http://www.example.com/1235", "#1235")]

def test_get_inherited_test_paths():
    class MySuite(lcc.TestSuite):
        class MySubSuite(lcc.TestSuite):
            @lcc.test("Test 2")
            def test(self):
                pass
    
    suite = MySuite()
    suite.load()
    
    assert suite.get_sub_testsuites()[0].get_inherited_test_paths(suite.get_sub_testsuites()[0].get_tests()[0]) \
        == ["MySuite", "MySuite.MySubSuite", "MySuite.MySubSuite.test"]

def test_get_inherited_test_descriptions():
    class MySuite(lcc.TestSuite):
        description = "My suite"
        class MySubSuite(lcc.TestSuite):
            description = "My sub suite"
            @lcc.test("Test")
            def test(self):
                pass
    
    suite = MySuite()
    suite.load()
    
    assert suite.get_sub_testsuites()[0].get_inherited_test_descriptions(suite.get_sub_testsuites()[0].get_tests()[0]) \
        == ["My suite", "My sub suite", "Test"]
