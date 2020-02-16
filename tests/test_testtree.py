import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.suite import load_suites_from_classes, load_suite_from_class
from lemoncheesecake.testtree import find_suite, find_test, flatten_suites, flatten_tests


def test_hierarchy():
    @lcc.suite("My suite")
    class mysuite:
        @lcc.test("My test")
        def mytest(self):
            pass

    suite = load_suite_from_class(mysuite)
    test = suite.get_tests()[0]

    path = test.hierarchy
    assert next(path).name == "mysuite"
    assert next(path).name == "mytest"


def test_get_path_on_nested_suite():
    @lcc.suite("My suite")
    class mysuite:
        @lcc.suite("My sub suite")
        class mysubsuite:
            @lcc.test("My test")
            def mytest(self):
                pass

    suite = load_suite_from_class(mysuite)
    test = suite.get_suites()[0].get_tests()[0]

    path = test.hierarchy
    assert next(path).name == "mysuite"
    assert next(path).name == "mysubsuite"
    assert next(path).name == "mytest"


def test_hierarchy_depth():
    @lcc.suite("My suite")
    class mysuite:
        @lcc.test("My test")
        def mytest(self):
            pass

    suite = load_suite_from_class(mysuite)
    test = suite.get_tests()[0]

    assert test.hierarchy_depth == 1


def test_path():
    @lcc.suite("My suite")
    class mysuite:
        @lcc.test("My test")
        def mytest(self):
            pass

    suite = load_suite_from_class(mysuite)
    test = suite.get_tests()[0]

    assert test.path == "mysuite.mytest"


def test_hierarchy_tags():
    @lcc.tags("tag1")
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.suite("MySubSuite")
        class MySubSuite:
            @lcc.tags("tag2")
            @lcc.test("Test 2")
            def test(self):
                pass

    suite = load_suite_from_class(MySuite)

    assert suite.get_suites()[0].get_tests()[0].hierarchy_tags == ["tag1", "tag2"]


def test_hierarchy_properties():
    @lcc.prop("prop1", "foo")
    @lcc.prop("prop2", "bar")
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.prop("prop3", "foobar")
        @lcc.suite("MySubSuite")
        class MySubSuite:
            @lcc.prop("prop1", "baz")
            @lcc.test("Test 2")
            def test(self):
                pass

    suite = load_suite_from_class(MySuite)

    assert suite.get_suites()[0].get_tests()[0].hierarchy_properties == {"prop1": "baz", "prop2": "bar", "prop3": "foobar"}


def test_hierarchy_links():
    @lcc.link("http://www.example.com/1234")
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.suite("MySubSuite")
        class MySubSuite:
            @lcc.link("http://www.example.com/1235", "#1235")
            @lcc.test("Test 2")
            def test(self):
                pass

    suite = load_suite_from_class(MySuite)

    assert suite.get_suites()[0].get_tests()[0].hierarchy_links == [("http://www.example.com/1234", None), ("http://www.example.com/1235", "#1235")]


def test_hierarchy_paths():
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.suite("MySubSuite")
        class MySubSuite:
            @lcc.test("Test 2")
            def test(self):
                pass

    suite = load_suite_from_class(MySuite)

    assert list(suite.get_suites()[0].get_tests()[0].hierarchy_paths) == ["MySuite", "MySuite.MySubSuite", "MySuite.MySubSuite.test"]


def test_hierarchy_descriptions():
    @lcc.suite("My suite")
    class MySuite:
        @lcc.suite("My sub suite")
        class MySubSuite:
            @lcc.test("Test")
            def test(self):
                pass

    suite = load_suite_from_class(MySuite)

    assert list(suite.get_suites()[0].get_tests()[0].hierarchy_descriptions) == ["My suite", "My sub suite", "Test"]


def test_flatten_suites():
    @lcc.suite("My suite 1")
    class mysuite1:
        @lcc.test("Test 1")
        def test1(self):
            pass

    @lcc.suite("My suite 2")
    class mysuite2:
        @lcc.test("Test 2")
        def test2(self):
            pass

    suites = load_suites_from_classes([mysuite1, mysuite2])

    flattened_suites = flatten_suites(suites)

    assert [s.name for s in flattened_suites] == ["mysuite1", "mysuite2"]


def test_flatten_suites_on_nested_suites():
    @lcc.suite("My suite 1")
    class mysuite1:
        @lcc.suite("My suite 2")
        class mysuite2:
            @lcc.test("Test")
            def test(self):
                pass

    @lcc.suite("My suite 3")
    class mysuite3:
        @lcc.suite("My suite 4")
        class mysuite4:
            @lcc.test("Test")
            def test(self):
                pass

    suites = load_suites_from_classes([mysuite1, mysuite3])

    flattened_suites = flatten_suites(suites)

    assert [s.name for s in flattened_suites] == ["mysuite1", "mysuite2", "mysuite3", "mysuite4"]


def test_flatten_tests():
    @lcc.suite("My suite 1")
    class mysuite1:
        @lcc.test("Test 1")
        def test1(self):
            pass

    @lcc.suite("My suite 2")
    class mysuite2:
        @lcc.test("Test 2")
        def test2(self):
            pass

    suites = load_suites_from_classes([mysuite1, mysuite2])

    tests = flatten_tests(suites)

    assert [t.name for t in tests] == ["test1", "test2"]


def test_flatten_tests_on_nested_suites():
    @lcc.suite("My suite 1")
    class mysuite1:
        @lcc.test("Test 1")
        def test1(self):
            pass

        @lcc.suite("My suite 2")
        class mysuite2:
            @lcc.test("Test 2")
            def test2(self):
                pass

    @lcc.suite("My suite 3")
    class mysuite3:
        @lcc.test("Test 3")
        def test3(self):
            pass

        @lcc.suite("My suite 4")
        class mysuite4:
            @lcc.test("Test 4")
            def test4(self):
                pass

    suites = load_suites_from_classes([mysuite1, mysuite3])

    tests = flatten_tests(suites)

    assert [t.name for t in tests] == ["test1", "test2", "test3", "test4"]


def test_find_suite_top():
    @lcc.suite("My suite 1")
    class mysuite1:
        pass

    @lcc.suite("My suite 2")
    class mysuite2:
        pass

    suites = load_suites_from_classes([mysuite1, mysuite2])
    suite = find_suite(suites, "mysuite2")
    assert suite.name == "mysuite2"


def test_find_suite_nested():
    @lcc.suite("My suite 1")
    class mysuite1:
        @lcc.suite("My suite 2")
        class mysuite2:
            pass

    suites = load_suites_from_classes([mysuite1])
    suite = find_suite(suites, "mysuite1.mysuite2")
    assert suite.name == "mysuite2"


def test_find_suite_unknown():
    @lcc.suite("My suite 1")
    class mysuite1:
        pass

    suites = load_suites_from_classes([mysuite1])

    with pytest.raises(LookupError):
        find_suite(suites, "unknownsuite")


def test_find_test():
    @lcc.suite("My suite 1")
    class mysuite1:
        @lcc.test("My test")
        def mytest(self):
            pass

    suites = load_suites_from_classes([mysuite1])
    test = find_test(suites, "mysuite1.mytest")
    assert test.name == "mytest"


def test_find_test_unknown():
    @lcc.suite("My suite 1")
    class mysuite1:
        @lcc.test("My test")
        def mytest(self):
            pass

    suites = load_suites_from_classes([mysuite1])

    with pytest.raises(LookupError):
        find_test(suites, "mysuite1.unknown")


def test_is_empty_on_suite_with_test():
    @lcc.suite("My suite 1")
    class mysuite1:
        @lcc.test("My test")
        def mytest(self):
            pass

    suite = load_suite_from_class(mysuite1)

    assert not suite.is_empty()


def test_is_empty_on_sub_suite_with_test():
    @lcc.suite("My suite 1")
    class mysuite1:
        @lcc.suite("My suite 2")
        class mysuite2:
            @lcc.test("My test")
            def mytest(self):
                pass

    suite = load_suite_from_class(mysuite1)

    assert not suite.is_empty()


def test_is_empty_on_suite_without_test():
    @lcc.suite("My suite 1")
    class mysuite1:
        pass

    suite = load_suite_from_class(mysuite1)

    assert suite.is_empty()


def test_pull_test_node():
    @lcc.suite("My suite 1")
    class mysuite1:
        @lcc.test("My test")
        def mytest(self):
            pass

    suite = load_suite_from_class(mysuite1)

    test = suite.get_tests()[0]
    pulled_test = test.pull_node()

    assert pulled_test.parent_suite is None
    assert test.parent_suite is not None


def test_pull_test_suite_top():
    @lcc.suite("My suite 1")
    class mysuite1:
        @lcc.test("My test")
        def mytest(self):
            pass

    suite = load_suite_from_class(mysuite1)

    pulled_suite = suite.pull_node()

    assert pulled_suite.parent_suite is None
    assert len(pulled_suite.get_tests()) == 0

    assert suite.parent_suite is None
    assert len(suite.get_tests()) == 1


def test_pull_test_suite():
    @lcc.suite("My suite 1")
    class mysuite1:
        @lcc.suite("My suite 2")
        class mysuite2:
            @lcc.test("My test")
            def mytest(self):
                pass

    top_suite = load_suite_from_class(mysuite1)
    sub_suite = top_suite.get_suites()[0]

    pulled_suite = sub_suite.pull_node()

    assert pulled_suite.parent_suite is None
    assert len(pulled_suite.get_tests()) == 0

    assert sub_suite.parent_suite is not None
    assert len(sub_suite.get_tests()) == 1
