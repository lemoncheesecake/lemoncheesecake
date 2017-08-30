import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.suite import load_suites_from_classes
from lemoncheesecake.testtree import find_suite, find_test
from lemoncheesecake.exceptions import CannotFindTreeNode


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
