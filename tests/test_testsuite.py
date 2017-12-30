 # -*- coding: utf-8 -*-

'''
Created on Sep 30, 2016

@author: nicolas
'''

import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.suite import load_suite_from_class, add_test_in_suite, add_tests_in_suite
from lemoncheesecake.exceptions import ProgrammingError, InvalidMetadataError

from helpers import dummy_test_callback


def test_decorator_test():
    @lcc.suite("My Suite")
    class MySuite:
        @lcc.test("test_desc")
        def mytest(self):
            pass
    suite = load_suite_from_class(MySuite)
    test = suite.get_tests()[0]
    assert test.name == "mytest"
    assert test.description == "test_desc"


def test_decorator_test_with_name():
    @lcc.test("My Test", name="mytest")
    def sometest():
        pass

    metadata = lcc.get_metadata(sometest)
    assert metadata.name == "mytest"


def test_decorator_tags():
    @lcc.suite("My Suite")
    @lcc.tags("tag3")
    class MySuite:
        @lcc.test("test_desc")
        @lcc.tags("tag1", "tag2")
        def mytest(self):
            pass
    suite = load_suite_from_class(MySuite)
    assert suite.tags == ["tag3"]
    test = suite.get_tests()[0]
    assert test.tags == ["tag1", "tag2"]


def test_decorator_prop():
    @lcc.suite("My Suite")
    @lcc.prop("key1", "val1")
    class MySuite:
        @lcc.test("test_desc")
        @lcc.prop("key2", "val2")
        def mytest(self):
            pass
    suite = load_suite_from_class(MySuite)
    assert suite.properties["key1"] == "val1"
    test = suite.get_tests()[0]
    assert test.properties["key2"] == "val2"


def test_decorator_link():
    @lcc.suite("My Suite")
    @lcc.link("http://www.example.com", "example")
    class MySuite:
        @lcc.test("test_desc")
        @lcc.link("http://www.example.com")
        def mytest(self):
            pass
    suite = load_suite_from_class(MySuite)
    assert suite.links[0] == ("http://www.example.com", "example")
    test = suite.get_tests()[0]
    assert test.links[0] == ("http://www.example.com", None)


def test_test_decorator_on_invalid_object():
    with pytest.raises(ProgrammingError):
        @lcc.test("test")
        class NotAFunction():
            pass


def test_decorator_suite_with_name():
    @lcc.test("My Suite", name="mysuite")
    def somesuite():
        pass

    metadata = lcc.get_metadata(somesuite)
    assert metadata.name == "mysuite"


def test_suite_decorator_on_invalid_object():
    with pytest.raises(ProgrammingError):
        @lcc.suite("suite")
        def NotAClass():
            pass


def test_decorator_with_suite_inheritance():
    @lcc.suite("My Suite 1")
    @lcc.link("http://www.example1.com")
    @lcc.tags("tag1", "tag2")
    @lcc.prop("key1", "value1")
    class MySuite1:
        pass

    @lcc.suite("My Suite 2")
    @lcc.link("http://www.example2.com")
    @lcc.tags("tag3")
    @lcc.prop("key2", "value2")
    class MySuite2(MySuite1):
        pass

    suite1 = load_suite_from_class(MySuite1)
    suite2 = load_suite_from_class(MySuite2)

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
    @lcc.suite(u"My Suite éééààà")
    @lcc.link("http://foo.bar", u"éééààà")
    @lcc.prop(u"ééé", u"ààà")
    @lcc.tags(u"ééé", u"ààà")
    class MySuite:
        @lcc.test(u"Some test ààà")
        @lcc.link("http://foo.bar", u"éééààà")
        @lcc.prop(u"ééé", u"ààà")
        @lcc.tags(u"ééé", u"ààà")
        def sometest(self):
            pass

    suite = load_suite_from_class(MySuite)

    assert suite.links[0] == ("http://foo.bar", u"éééààà")
    assert suite.properties[u"ééé"] == u"ààà"
    assert suite.tags == [u"ééé", u"ààà"]

    test = suite.get_tests()[0]
    assert test.description == u"Some test ààà"
    assert test.links[0] == ("http://foo.bar", u"éééààà")
    assert test.properties[u"ééé"] == u"ààà"
    assert test.tags == [u"ééé", u"ààà"]


def test_duplicated_suite_description():
    @lcc.suite("My Suite")
    class MySuite:
        @lcc.suite("somedesc")
        class SubSuite1:
            pass
        @lcc.suite("somedesc")
        class SubSuite2:
            pass

    with pytest.raises(InvalidMetadataError) as excinfo:
        load_suite_from_class(MySuite)


def test_duplicated_test_description():
    @lcc.suite("My Suite")
    class MySuite:
        @lcc.test("somedesc")
        def foo(self):
            pass

        @lcc.test("somedesc")
        def bar(self):
            pass

    with pytest.raises(InvalidMetadataError):
        load_suite_from_class(MySuite)


def test_duplicated_test_name():
    @lcc.suite("My Suite")
    class MySuite:
        def __init__(self):
            add_test_in_suite(lcc.Test("mytest", "First test", dummy_test_callback()), self)
            add_test_in_suite(lcc.Test("mytest", "Second test", dummy_test_callback()), self)

    with pytest.raises(ProgrammingError):
        load_suite_from_class(MySuite)


def test_suite_rank():
    @lcc.suite("My Suite")
    class MySuite1:
        @lcc.suite("D")
        class D:
            @lcc.test("test")
            def test(self): pass

        @lcc.suite("C")
        class C:
            @lcc.test("test")
            def test(self): pass

        @lcc.suite("B")
        class B:
            @lcc.test("test")
            def test(self): pass

        @lcc.suite("A")
        class A:
            @lcc.test("test")
            def test(self): pass

    suite = load_suite_from_class(MySuite1)

    assert suite.get_suites()[0].name == "D"
    assert suite.get_suites()[1].name == "C"
    assert suite.get_suites()[2].name == "B"
    assert suite.get_suites()[3].name == "A"


def test_suite_rank_forced():
    @lcc.suite("My Suite")
    class MySuite1:
        @lcc.suite("A", rank=2)
        class A:
            @lcc.test("test")
            def test(self): pass

        @lcc.suite("B", rank=3)
        class B:
            @lcc.test("test")
            def test(self): pass

        @lcc.suite("C", rank=1)
        class C:
            @lcc.test("test")
            def test(self): pass

        @lcc.suite("D", rank=4)
        class D:
            @lcc.test("test")
            def test(self): pass

    suite = load_suite_from_class(MySuite1)

    assert suite.get_suites()[0].name == "C"
    assert suite.get_suites()[1].name == "A"
    assert suite.get_suites()[2].name == "B"
    assert suite.get_suites()[3].name == "D"


def test_register_test():
    @lcc.suite("My Suite")
    class MySuite:
        def __init__(self):
            add_test_in_suite(lcc.Test("mytest", "My Test", dummy_test_callback()), self)

    suite = load_suite_from_class(MySuite)
    assert len(suite.get_tests()) == 1


def test_register_test_multiple():
    @lcc.suite("My Suite")
    class MySuite:
        def __init__(self):
            for i in 1, 2, 3:
                add_test_in_suite(lcc.Test("mytest_%d" % i, "My Test %d" % i, dummy_test_callback()), self)

    suite = load_suite_from_class(MySuite)
    assert len(suite.get_tests()) == 3


def test_register_disabled():
    @lcc.suite("My Suite")
    class MySuite:
        def __init__(self):
            test = lcc.Test("mytest", "My Test", dummy_test_callback())
            test.disabled = True
            add_test_in_suite(test, self)

    suite = load_suite_from_class(MySuite)
    test = suite.get_tests()[0]
    assert test.is_disabled()


def test_register_test_with_before_and_after():
    @lcc.suite("My Suite")
    class MySuite:
        def __init__(self):
            add_test_in_suite(lcc.Test("foo1", "Foo 1", dummy_test_callback()), self, before_test="bar1")
            add_test_in_suite(lcc.Test("foo2", "Foo 2", dummy_test_callback()), self, before_test="bar1")
            add_test_in_suite(lcc.Test("baz1", "Baz 1", dummy_test_callback()), self, after_test="bar2")
            add_test_in_suite(lcc.Test("baz2", "Baz 2", dummy_test_callback()), self, after_test="baz1")

        @lcc.test("Bar 1")
        def bar1(self):
            pass

        @lcc.test("Bar 2")
        def bar2(self):
            pass

    suite = load_suite_from_class(MySuite)

    assert [t.name for t in suite.get_tests()] == ["foo1", "foo2", "bar1", "bar2", "baz1", "baz2"]


def test_register_tests_with_before_and_after():
    @lcc.suite("My Suite")
    class MySuite:
        def __init__(self):
            add_tests_in_suite(
                [lcc.Test("foo1", "Foo 1", dummy_test_callback()), lcc.Test("foo2", "Foo 2", dummy_test_callback())],
                self, before_test="bar1"
            )
            add_tests_in_suite(
                [lcc.Test("baz1", "Baz 1", dummy_test_callback()), lcc.Test("baz2", "Baz 2", dummy_test_callback())],
                self, after_test="bar2"
            )

        @lcc.test("Bar 1")
        def bar1(self):
            pass

        @lcc.test("Bar 2")
        def bar2(self):
            pass

    suite = load_suite_from_class(MySuite)

    assert [t.name for t in suite.get_tests()] == ["foo1", "foo2", "bar1", "bar2", "baz1", "baz2"]


def test_get_fixtures():
    @lcc.suite("My Suite")
    class MySuite:
        def setup_suite(self, foo):
            pass

    suite = load_suite_from_class(MySuite)

    assert suite.get_fixtures() == ["foo"]

