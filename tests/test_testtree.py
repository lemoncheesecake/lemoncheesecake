import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.suite import load_suites_from_classes, load_suite_from_class
from lemoncheesecake.testtree import find_suite, find_test
from lemoncheesecake.exceptions import CannotFindTreeNode


def test_get_path():
    @lcc.suite("My suite")
    class mysuite:
        @lcc.test("My test")
        def mytest(self):
            pass

    suite = load_suite_from_class(mysuite)
    test = suite.get_tests()[0]

    path = test.get_path()
    assert next(path).name == "mysuite"
    assert next(path).name == "mytest"


def test_get_path_nested_suite():
    @lcc.suite("My suite")
    class mysuite:
        @lcc.suite("My sub suite")
        class mysubsuite:
            @lcc.test("My test")
            def mytest(self):
                pass

    suite = load_suite_from_class(mysuite)
    test = suite.get_suites()[0].get_tests()[0]

    path = test.get_path()
    assert next(path).name == "mysuite"
    assert next(path).name == "mysubsuite"
    assert next(path).name == "mytest"


def test_get_depth():
    @lcc.suite("My suite")
    class mysuite:
        @lcc.test("My test")
        def mytest(self):
            pass

    suite = load_suite_from_class(mysuite)
    test = suite.get_tests()[0]

    assert test.get_depth() == 1


def test_path():
    @lcc.suite("My suite")
    class mysuite:
        @lcc.test("My test")
        def mytest(self):
            pass

    suite = load_suite_from_class(mysuite)
    test = suite.get_tests()[0]

    assert test.path == "mysuite.mytest"


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

    with pytest.raises(CannotFindTreeNode):
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

    with pytest.raises(CannotFindTreeNode):
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
