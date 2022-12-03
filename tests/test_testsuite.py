 # -*- coding: utf-8 -*-

'''
Created on Sep 30, 2016

@author: nicolas
'''

import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.suite import load_suite_from_class, add_test_into_suite, resolve_tests_dependencies
from lemoncheesecake.exceptions import SuiteLoadingError, ValidationError

from helpers.runner import dummy_test_callback, build_suite_from_module


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


def test_decorator_test_without_description():
    @lcc.suite("My Suite")
    class MySuite:
        @lcc.test()
        def my_test(self):
            pass

    suite = load_suite_from_class(MySuite)
    test = suite.get_tests()[0]
    assert test.name == "my_test"
    assert test.description == "My test"


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
    with pytest.raises(AssertionError):
        @lcc.test("test")
        class NotAFunction:
            pass


def test_decorator_suite_with_name():
    @lcc.suite("My Suite", name="mysuite")
    class somesuite():
        pass

    suite = load_suite_from_class(somesuite)
    assert suite.name == "mysuite"


def test_decorator_suite_without_description():
    @lcc.suite()
    class some_suite():
        pass

    suite = load_suite_from_class(some_suite)
    assert suite.description == "Some suite"


def test_suite_decorator_on_invalid_object():
    with pytest.raises(AssertionError):
        @lcc.suite("suite")
        def not_a_class():
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
    @lcc.suite("My Suite éééààà")
    @lcc.link("http://foo.bar", "éééààà")
    @lcc.prop("ééé", "ààà")
    @lcc.tags("ééé", "ààà")
    class MySuite:
        @lcc.test("Some test ààà")
        @lcc.link("http://foo.bar", "éééààà")
        @lcc.prop("ééé", "ààà")
        @lcc.tags("ééé", "ààà")
        def sometest(self):
            pass

    suite = load_suite_from_class(MySuite)

    assert suite.links[0] == ("http://foo.bar", "éééààà")
    assert suite.properties["ééé"] == "ààà"
    assert suite.tags == ["ééé", "ààà"]

    test = suite.get_tests()[0]
    assert test.description == "Some test ààà"
    assert test.links[0] == ("http://foo.bar", "éééààà")
    assert test.properties["ééé"] == "ààà"
    assert test.tags == ["ééé", "ààà"]


def test_duplicated_suite_description():
    @lcc.suite("My Suite")
    class MySuite:
        @lcc.suite("somedesc")
        class SubSuite1:
            pass
        @lcc.suite("somedesc")
        class SubSuite2:
            pass

    with pytest.raises(SuiteLoadingError, match="is already registered"):
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

    with pytest.raises(SuiteLoadingError, match="is already registered"):
        load_suite_from_class(MySuite)


def test_duplicated_test_name():
    @lcc.suite("My Suite")
    class MySuite:
        def __init__(self):
            add_test_into_suite(lcc.Test("mytest", "First test", dummy_test_callback()), self)
            add_test_into_suite(lcc.Test("mytest", "Second test", dummy_test_callback()), self)

    with pytest.raises(SuiteLoadingError, match="is already registered"):
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


def test_add_test_into_suite_with_function():
    def func():
        pass

    @lcc.suite("My Suite")
    class MySuite:
        def __init__(self):
            add_test_into_suite(lcc.Test("mytest", "My Test", func), self)

    suite = load_suite_from_class(MySuite)
    assert len(suite.get_tests()) == 1


def test_add_test_into_suite_with_function_and_fixture():
     def func(fixt):
         pass

     @lcc.suite("My Suite")
     class MySuite:
         def __init__(self):
             add_test_into_suite(lcc.Test("mytest", "My Test", func), self)

     suite = load_suite_from_class(MySuite)
     assert suite.get_tests()[0].get_fixtures() == ["fixt"]


def test_add_test_into_suite_with_method():
    @lcc.suite("My Suite")
    class MySuite:
        def __init__(self):
            add_test_into_suite(lcc.Test("mytest", "My Test", self.func), self)

        def func(self):
            pass

    suite = load_suite_from_class(MySuite)
    assert len(suite.get_tests()) == 1


def test_add_test_into_suite_with_method_and_fixture():
     @lcc.suite("My Suite")
     class MySuite:
        def __init__(self):
             add_test_into_suite(lcc.Test("mytest", "My Test", self.func), self)

        def func(self, fixt):
            pass

     suite = load_suite_from_class(MySuite)
     assert suite.get_tests()[0].get_fixtures() == ["fixt"]


def test_add_test_into_suite_with_callable():
    class SomeTest(object):
        def __call__(self):
            pass

    @lcc.suite("My Suite")
    class MySuite:
        def __init__(self):
            add_test_into_suite(lcc.Test("mytest", "My Test", SomeTest()), self)

    suite = load_suite_from_class(MySuite)
    assert len(suite.get_tests()) == 1


def test_add_test_into_suite_with_callable_and_fixture():
    class SomeTest(object):
        def __call__(self, fixt):
            pass

    @lcc.suite("My Suite")
    class MySuite:
        def __init__(self):
            add_test_into_suite(lcc.Test("mytest", "My Test", SomeTest()), self)

    suite = load_suite_from_class(MySuite)
    assert suite.get_tests()[0].get_fixtures() == ["fixt"]


def test_add_test_into_suite_multiple():
    @lcc.suite("My Suite")
    class MySuite:
        def __init__(self):
            for i in 1, 2, 3:
                add_test_into_suite(lcc.Test("mytest_%d" % i, "My Test %d" % i, dummy_test_callback()), self)

    suite = load_suite_from_class(MySuite)
    assert len(suite.get_tests()) == 3


def test_add_test_into_suite_disabled():
    @lcc.suite("My Suite")
    class MySuite:
        def __init__(self):
            test = lcc.Test("mytest", "My Test", dummy_test_callback())
            test.disabled = True
            add_test_into_suite(test, self)

    suite = load_suite_from_class(MySuite)
    test = suite.get_tests()[0]
    assert test.is_disabled()


def test_add_test_into_module():
    suite = build_suite_from_module("""
import sys

def func():
    pass

lcc.add_test_into_suite(lcc.Test("test", "Test", func), sys.modules[__name__])
""")

    assert len(suite.get_tests()) == 1


def test_get_fixtures():
    @lcc.suite("My Suite")
    class MySuite:
        def setup_suite(self, foo):
            pass

    suite = load_suite_from_class(MySuite)

    assert suite.get_fixtures() == ["foo"]


def test_depends_on_test():
    @lcc.suite("suite")
    class suite:
        @lcc.test("My Test")
        @lcc.depends_on("another.test")
        def test(self):
            pass

    suite = load_suite_from_class(suite)
    test = suite.get_tests()[0]

    assert test.dependencies == ["another.test"]


def test_depends_on_suite():
    with pytest.raises(AssertionError):
        @lcc.suite("suite")
        @lcc.depends_on("another.suite")
        class suite:
            @lcc.test("My Test")
            def test(self):
                pass


def test_resolve_test_dependencies():
    @lcc.suite()
    class suite:
        @lcc.test()
        def test_1(self):
            pass

        @lcc.test()
        @lcc.depends_on("suite.test_1")
        def test_2(self):
            pass

    suite = load_suite_from_class(suite)
    resolve_tests_dependencies([suite], [suite])
    assert suite.get_test_by_name("test_2").resolved_dependencies[0].path == "suite.test_1"


def test_resolve_test_dependencies_with_callable():
    @lcc.suite()
    class suite:
        @lcc.test()
        def test_1(self):
            pass

        @lcc.test()
        @lcc.depends_on(lambda test: test.path == "suite.test_1")
        def test_2(self):
            pass

    suite = load_suite_from_class(suite)
    resolve_tests_dependencies([suite], [suite])
    assert suite.get_test_by_name("test_2").resolved_dependencies[0].path == "suite.test_1"


def test_resolve_tests_dependencies_with_unknown_test():
    @lcc.suite()
    class suite:
        @lcc.test()
        @lcc.depends_on("another.test")
        def test(self):
            pass

    suite = load_suite_from_class(suite)

    with pytest.raises(ValidationError):
        resolve_tests_dependencies([suite], [suite])


def test_resolve_tests_dependencies_circular_dependency_direct():
    @lcc.suite()
    class suite:
        @lcc.test()
        @lcc.depends_on("suite.test")
        def test(self):
            pass

    suite = load_suite_from_class(suite)

    with pytest.raises(ValidationError):
        resolve_tests_dependencies([suite], [suite])


def test_resolve_tests_dependencies_circular_dependency_indirect():
    @lcc.suite()
    class suite:
        @lcc.test()
        @lcc.depends_on("suite.test_3")
        def test_1(self):
            pass

        @lcc.test()
        @lcc.depends_on("suite.test_1")
        def test_2(self):
            pass

        @lcc.test()
        @lcc.depends_on("suite.test_2")
        def test_3(self):
            pass

    suite = load_suite_from_class(suite)

    with pytest.raises(ValidationError):
        resolve_tests_dependencies([suite], [suite])
