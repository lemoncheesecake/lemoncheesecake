import os.path

import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.suite.loader import load_suites_from_directory, load_suite_from_file, \
    load_suite_from_class, load_suites_from_files, load_suites_from_classes, load_test_from_function, \
    load_test_from_method, is_test_function
from lemoncheesecake.validators import MetadataPolicy
from lemoncheesecake.exceptions import *
from helpers import build_test_module

def test_load_suite_from_file(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(build_test_module())
    klass = load_suite_from_file(file.strpath)
    assert klass.name == "mysuite"

def test_load_suite_from_file_invalid_module(tmpdir):
    file = tmpdir.join("doesnotexist.py")
    with pytest.raises(ImportSuiteError):
        load_suite_from_file(file.strpath)

def test_load_suite_from_file_invalid_class(tmpdir):
    file = tmpdir.join("anothersuite.py")
    file.write(build_test_module())
    with pytest.raises(ImportSuiteError):
        load_suite_from_file(file.strpath)

def test_load_suites_from_directory_without_modules(tmpdir):
    klasses = load_suites_from_directory(tmpdir.strpath)
    assert len(klasses) == 0

def test_load_suites_from_directory_with_modules(tmpdir):
    names = []
    for i in range(3):
        name = "mysuite%d" % i
        names.append(name)
        tmpdir.join("%s.py" % name).write(build_test_module(name))
    klasses = load_suites_from_directory(tmpdir.strpath)
    for name in names:
        assert name in [k.name for k in klasses]

def test_load_suites_from_directory_with_subdir(tmpdir):
    file = tmpdir.join("parentsuite.py")
    file.write(build_test_module("parentsuite"))
    subdir = tmpdir.join("parentsuite")
    subdir.mkdir()
    file = subdir.join("childsuite.py")
    file.write(build_test_module("childsuite"))
    klasses = load_suites_from_directory(tmpdir.strpath)
    assert klasses[0].name == "parentsuite"
    assert len(klasses[0].get_suites()) == 1

def test_load_suites_from_files(tmpdir):
    for name in "suite1", "suite2", "mysuite":
        tmpdir.join(name + ".py").write(build_test_module(name))
    klasses = load_suites_from_files(tmpdir.join("suite*.py").strpath)
    assert len(klasses) == 2
    assert "suite1" in [k.name for k in klasses]
    assert "suite2" in [k.name for k in klasses]

def test_load_suites_from_files_nomatch(tmpdir):
    klasses = load_suites_from_files(tmpdir.join("*.py").strpath)
    assert len(klasses) == 0

def test_load_suites_from_files_exclude(tmpdir):
    for name in "suite1", "suite2", "mysuite":
        tmpdir.join(name + ".py").write(build_test_module(name))
    klasses = load_suites_from_files(tmpdir.join("*.py").strpath, "*/suite*.py")
    assert len(klasses) == 1
    assert klasses[0].name == "mysuite"

def test_load_suites_with_same_name():
    @lcc.suite("My Suite 1")
    class MySuite1:
        @lcc.suite("My Sub Suite 1")
        class MySubSuite:
            @lcc.test("foo")
            def foo(self):
                pass

    @lcc.suite("My Suite 2")
    class MySuite2:
        @lcc.suite("My Sub Suite 1")
        class MySubSuite:
            @lcc.test("bar")
            def bar(self):
                pass

    suites = load_suites_from_classes([MySuite1, MySuite2])

    assert suites[0].name == "MySuite1"
    assert suites[0].get_suites()[0].name == "MySubSuite"
    assert suites[1].name == "MySuite2"
    assert suites[1].get_suites()[0].name == "MySubSuite"

def test_load_tests_with_same_name():
    @lcc.suite("My Suite 1")
    class MySuite1:
        @lcc.suite("My Sub Suite 1")
        class MySubSuite1:
            @lcc.test("foo")
            def foo(self):
                pass

    @lcc.suite("My Suite 2")
    class MySuite2:
        @lcc.suite("My Sub Suite 2")
        class MySubSuite2:
            @lcc.test("foo")
            def foo(self):
                pass

    suites = load_suites_from_classes([MySuite1, MySuite2])

    assert suites[0].name == "MySuite1"
    assert suites[0].get_suites()[0].name == "MySubSuite1"
    assert suites[0].get_suites()[0].get_tests()[0].name == "foo"
    assert suites[1].name == "MySuite2"
    assert suites[1].get_suites()[0].name == "MySubSuite2"
    assert suites[1].get_suites()[0].get_tests()[0].name == "foo"

def test_metadata_policy():
    @lcc.suite("My Suite 1")
    class MySuite1:
        @lcc.prop("foo", 3)
        @lcc.test("Some test")
        def sometest(self):
            pass

    @lcc.suite("My Suite 1")
    @lcc.prop("foo", 3)
    class MySuite2:
        @lcc.test("Some test")
        def sometest(self):
            pass

    suite1 = load_suites_from_classes([MySuite1])
    suite2 = load_suites_from_classes([MySuite2])

    policy = MetadataPolicy()
    policy.add_property_rule("foo", (1, 2))
    with pytest.raises(InvalidMetadataError):
        policy.check_suites_compliance(suite1)
    with pytest.raises(InvalidMetadataError):
        policy.check_suites_compliance(suite2)

def test_load_test_from_function():
    @lcc.test("mytest")
    def func():
        return 1

    test = load_test_from_function(func)
    assert test.name == "func"
    assert test.description == "mytest"
    assert test.callback() == 1

def test_load_test_from_method():
    @lcc.suite("mysuite")
    class Suite:
        @lcc.test("mytest")
        def meth(self):
            return 1

    suite = Suite()
    test = load_test_from_method(suite.meth)
    assert test.name == "meth"
    assert test.description == "mytest"
    assert test.callback() == 1

def test_load_suite_from_class_with_hooks(tmpdir):
    @lcc.suite("mysuite")
    class Suite:
        def setup_suite(self):
            return 1

        def teardown_suite(self):
            return 2

        def setup_test(self, test_name):
            return 3

        def teardown_test(self, test_name):
            return 4

    suite = load_suite_from_class(Suite)
    assert suite.get_hook("setup_suite")() == 1
    assert suite.get_hook("teardown_suite")() == 2
    assert suite.get_hook("setup_test")("dummy") == 3
    assert suite.get_hook("teardown_test")("dummy") == 4

def test_load_suite_from_module(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """TESTSUITE = {
    "description": "My Suite"
}
""")
    suite = load_suite_from_file(file.strpath)
    assert suite.name == "mysuite"
    assert suite.description == "My Suite"

def test_load_suite_from_module_with_all_metadata(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """TESTSUITE = {
    "description": "My Suite",
    "tags": ["foo", "bar"],
    "properties": {"bar": "baz"},
    "links": [("http://u.r.l/1234", None), ("http://u.r.l/1235", "#1235")],
}
""")
    suite = load_suite_from_file(file.strpath)
    assert suite.name == "mysuite"
    assert suite.description == "My Suite"
    assert suite.tags == ["foo", "bar"]
    assert suite.properties == {"bar": "baz"}
    assert suite.links == [("http://u.r.l/1234", None), ("http://u.r.l/1235", "#1235")]

def test_load_suite_from_module_with_test_function(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """import lemoncheesecake.api as lcc

TESTSUITE = {
    "description": "My Suite"
}

@lcc.test('My Test')
def mytest():
    pass
""")
    suite = load_suite_from_file(file.strpath)
    test = suite.get_tests()[0]
    assert test.name == "mytest"
    assert test.description == "My Test"

def test_load_suite_from_module_with_test_function_and_fixtures(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """import lemoncheesecake.api as lcc

TESTSUITE = {
    "description": "My Suite"
}

@lcc.test('My Test')
def mytest(fixt1, fixt2):
    pass
""")
    suite = load_suite_from_file(file.strpath)
    test = suite.get_tests()[0]
    assert test.name == "mytest"
    assert test.description == "My Test"
    assert test.get_params() == ["fixt1", "fixt2"]

def test_load_suite_from_module_with_sub_suite(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """import lemoncheesecake.api as lcc

TESTSUITE = {
    "description": "My Suite"
}

@lcc.suite('Sub Suite')
class subsuite:
    @lcc.test("My Test")
    def mytest(self):
        pass
""")
    suite = load_suite_from_file(file.strpath)
    sub_suite = suite.get_suites()[0]
    assert sub_suite.name == "subsuite"
    assert sub_suite.description == "Sub Suite"

def test_load_suite_from_module_with_hooks(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """import lemoncheesecake.api as lcc

TESTSUITE = {
    "description": "My Suite"
}

def setup_suite():
    return 1

def teardown_suite():
    return 2

def setup_test(test_name):
    return 3

def teardown_test(test_name):
    return 4

@lcc.test('My Test')
def mytest():
    pass
""")
    suite = load_suite_from_file(file.strpath)
    assert suite.get_hook("setup_suite")() == 1
    assert suite.get_hook("teardown_suite")() == 2
    assert suite.get_hook("setup_test")("dummy") == 3
    assert suite.get_hook("teardown_test")("dummy") == 4

def test_load_suites_from_directory_with_suite_and_sub_suite(tmpdir):
    tmpdir.join("mysuite.py").write(
        """import lemoncheesecake.api as lcc

TESTSUITE = {
    "description": "My Suite"
}

@lcc.test('My Test')
def mytest1():
    pass
""")

    tmpdir.mkdir("mysuite").join("subsuite.py").write(
        """import lemoncheesecake.api as lcc

TESTSUITE = {
    "description": "Sub Suite"
}

@lcc.test('My Test')
def mytest2():
    pass
"""
)
    suites = load_suites_from_directory(tmpdir.strpath)
    suite = suites[0]
    sub_suite = suite.get_suites()[0]
    assert sub_suite.name == "subsuite"
    assert sub_suite.description == "Sub Suite"
    assert sub_suite.parent_suite == suite

def test_load_suite_from_module_missing_suite_definition(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write("")

    with pytest.raises(ImportSuiteError):
        load_suite_from_file(file.strpath)
