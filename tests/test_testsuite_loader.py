import inspect

import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.suite.loader import load_suites_from_directory, load_suite_from_file, \
    load_suite_from_class, load_suites_from_files, load_suites_from_classes, _load_test
from lemoncheesecake.metadatapolicy import MetadataPolicy
from lemoncheesecake.exceptions import *

from helpers.runner import build_test_module


def test_load_suite_from_file(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(build_test_module())
    suite = load_suite_from_file(file.strpath)
    assert suite.name == "mysuite"


def test_load_suite_from_file_invalid_module(tmpdir):
    file = tmpdir.join("doesnotexist.py")
    with pytest.raises(SuiteLoadingError):
        load_suite_from_file(file.strpath)


def test_load_suites_from_directory_without_modules(tmpdir):
    suites = load_suites_from_directory(tmpdir.strpath)
    assert len(suites) == 0


def test_load_suites_from_directory_with_modules(tmpdir):
    names = []
    for i in range(3):
        name = "mysuite%d" % i
        names.append(name)
        tmpdir.join("%s.py" % name).write(build_test_module(name))
    suites = load_suites_from_directory(tmpdir.strpath)
    assert suites[0].name == "mysuite0"
    assert suites[1].name == "mysuite1"
    assert suites[2].name == "mysuite2"


def test_load_suites_from_directory_with_subdir(tmpdir):
    file = tmpdir.join("parentsuite.py")
    file.write(build_test_module("parentsuite"))
    subdir = tmpdir.join("parentsuite")
    subdir.mkdir()
    file = subdir.join("childsuite.py")
    file.write(build_test_module("childsuite"))

    suites = load_suites_from_directory(tmpdir.strpath)
    assert suites[0].name == "parentsuite"
    assert len(suites[0].get_suites()) == 1
    assert suites[0].get_suites()[0].name == "childsuite"


def test_load_suites_from_directory_with_subdir_only(tmpdir):
    subdir = tmpdir.join("parentsuite")
    subdir.mkdir()
    file = subdir.join("childsuite.py")
    file.write(build_test_module("childsuite"))

    suites = load_suites_from_directory(tmpdir.strpath)
    assert suites[0].name == "parentsuite"
    assert suites[0].description == "Parentsuite"
    assert len(suites[0].get_suites()) == 1
    assert suites[0].get_suites()[0].name == "childsuite"


def test_load_suites_from_files(tmpdir):
    for name in "suite1", "suite2", "mysuite":
        tmpdir.join(name + ".py").write(build_test_module(name))
    suites = load_suites_from_files(tmpdir.join("suite*.py").strpath)
    assert len(suites) == 2
    assert suites[0].name == "suite1"
    assert suites[1].name == "suite2"


def test_load_suites_from_files_nomatch(tmpdir):
    suites = load_suites_from_files(tmpdir.join("*.py").strpath)
    assert len(suites) == 0


def test_load_suites_from_files_exclude(tmpdir):
    for name in "suite1", "suite2", "mysuite":
        tmpdir.join(name + ".py").write(build_test_module(name))
    suites = load_suites_from_files(tmpdir.join("*.py").strpath, "*/suite*.py")
    assert len(suites) == 1
    assert suites[0].name == "mysuite"


def test_load_suites_with_space_char_in_path(tmpdir):
    mod_path = tmpdir.mkdir("my dir").join("mysuite.py")
    mod_path.write(build_test_module())
    suite = load_suite_from_file(mod_path.strpath)
    assert suite.name == "mysuite"


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


def test_load_suite_from_class_tests_order():
    @lcc.suite("suite")
    class suite:
        @lcc.test("a")
        def a(self):
            pass

        @lcc.test("d")
        def d(self):
            pass

        @lcc.test("c")
        def c(self):
            pass

        @lcc.test("b")
        def b(self):
            pass

    suite = load_suite_from_class(suite)
    tests = suite.get_tests()

    assert tests[0].name == "a"
    assert tests[1].name == "d"
    assert tests[2].name == "c"
    assert tests[3].name == "b"


def test_load_suite_from_class_suites_order():
    @lcc.suite("suite")
    class suite:
        @lcc.suite("a")
        class a:
            @lcc.test("test")
            def test(self):
                pass

        @lcc.suite("d")
        class d:
            @lcc.test("test")
            def test(self):
                pass

        @lcc.suite("c")
        class c:
            @lcc.test("test")
            def test(self):
                pass

        @lcc.suite("b")
        class b:
            @lcc.test("test")
            def test(self):
                pass

    suite = load_suite_from_class(suite)
    suites = suite.get_suites()

    assert suites[0].name == "a"
    assert suites[1].name == "d"
    assert suites[2].name == "c"
    assert suites[3].name == "b"


def test_metadata_policy():
    @lcc.suite("My Suite 1")
    class MySuite1:
        @lcc.prop("foo", "3")
        @lcc.test("Some test")
        def sometest(self):
            pass

    @lcc.suite("My Suite 1")
    @lcc.prop("foo", "3")
    class MySuite2:
        @lcc.test("Some test")
        def sometest(self):
            pass

    suite1 = load_suites_from_classes([MySuite1])
    suite2 = load_suites_from_classes([MySuite2])

    policy = MetadataPolicy()
    policy.add_property_rule("foo", ("1", "2"))
    with pytest.raises(ValidationError):
        policy.check_suites_compliance(suite1)
    with pytest.raises(ValidationError):
        policy.check_suites_compliance(suite2)


def test_load_suites_from_classes_with_condition_on_suite_met():
    @lcc.suite("My Suite")
    @lcc.visible_if(lambda suite_arg: suite_arg.__class__ == MySuite)
    class MySuite:
        @lcc.test("My Test")
        def mytest(self):
            pass

    suites = load_suites_from_classes([MySuite])

    assert len(suites) == 1


def test_load_suites_from_classes_with_condition_on_suite_not_met():
    @lcc.suite("My Suite")
    @lcc.visible_if(lambda suite_arg: suite_arg.__class__ != MySuite)
    class MySuite:
        @lcc.test("My Test")
        def mytest(self):
            pass

    suites = load_suites_from_classes([MySuite])

    assert len(suites) == 0


def test_load_suites_from_classes_with_condition_on_test_met():
    @lcc.suite("My Suite")
    class MySuite:
        @lcc.test("My Test")
        @lcc.visible_if(lambda test_arg: test_arg.__func__ == MySuite.mytest)
        def mytest(self):
            pass

    suites = load_suites_from_classes([MySuite])

    assert len(suites[0].get_tests()) == 1


def test_load_suites_from_classes_with_condition_on_test_not_met():
    @lcc.suite("My Suite")
    class MySuite:
        @lcc.test("My Test")
        @lcc.visible_if(lambda test_arg: test_arg.__func__ != MySuite.mytest)
        def mytest(self):
            pass

    suites = load_suites_from_classes([MySuite])

    assert len(suites[0].get_tests()) == 0


def test_load_parametrized_test():
    @lcc.suite("suite")
    class MySuite:
        @lcc.test("test")
        @lcc.parametrized(({"value": 1}, {"value": 2}))
        @lcc.tags("mytag")
        def test(self, value):
            pass

    suite = load_suite_from_class(MySuite)

    tests = suite.get_tests()
    assert len(tests) == 2
    assert tests[0].name == "test_1"
    assert tests[0].description == "test #1"
    assert tests[0].tags == ["mytag"]
    assert tests[1].name == "test_2"
    assert tests[1].description == "test #2"
    assert tests[1].tags == ["mytag"]


def test_load_parametrized_test_no_parameters():
    @lcc.suite()
    class MySuite:
        @lcc.test()
        @lcc.parametrized(())
        def test(self, value):
            pass

    suite = load_suite_from_class(MySuite)

    tests = suite.get_tests()
    assert len(tests) == 0


def test_load_parametrized_test_csv_like():
    @lcc.suite("suite")
    class MySuite:
        @lcc.test("test")
        @lcc.parametrized(("i,j", (1, 2), (3, 4)))
        def test(self, i, j):
            pass

    suite = load_suite_from_class(MySuite)

    tests = suite.get_tests()
    assert len(tests) == 2
    assert tests[0].name == "test_1"
    assert tests[0].description == "test #1"
    assert tests[1].name == "test_2"
    assert tests[1].description == "test #2"


def test_load_parametrized_test_csv_like_with_header_as_tuple():
    @lcc.suite("suite")
    class MySuite:
        @lcc.test("test")
        @lcc.parametrized((("i", "j"), (1, 2), (3, 4)))
        def test(self, i, j):
            pass

    suite = load_suite_from_class(MySuite)

    tests = suite.get_tests()
    assert len(tests) == 2
    assert tests[0].name == "test_1"
    assert tests[0].description == "test #1"
    assert tests[1].name == "test_2"
    assert tests[1].description == "test #2"


def test_load_parametrized_test_from_iterator():
    def my_iterator():
        yield {"value": 1}
        yield {"value": 2}

    @lcc.suite("suite")
    class MySuite:
        @lcc.test("test")
        @lcc.parametrized(my_iterator())
        def test(self, value):
            pass

    suite = load_suite_from_class(MySuite)

    tests = suite.get_tests()
    assert len(tests) == 2
    assert tests[0].name == "test_1"
    assert tests[0].description == "test #1"
    assert tests[1].name == "test_2"
    assert tests[1].description == "test #2"


def test_load_parametrized_test_custom_naming():
    def naming_scheme(name, description, parameters, idx):
        return "%s_%s" % (name, parameters["value"]), "%s %s" % (description, parameters["value"])

    @lcc.suite("suite")
    class MySuite:
        @lcc.test("test")
        @lcc.parametrized(({"value": "foo"},), naming_scheme)
        def test(self, value):
            pass

    suite = load_suite_from_class(MySuite)
    test = suite.get_tests()[0]

    assert test.name == "test_foo"
    assert test.description == "test foo"


def test_load_parametrized_test_custom_naming_with_format():
    @lcc.suite("suite")
    class MySuite:
        @lcc.test()
        @lcc.parametrized(({"value": "foo"},), ("test_{value}", "test {value}"))
        def test(self, value):
            pass

    suite = load_suite_from_class(MySuite)
    test = suite.get_tests()[0]

    assert test.name == "test_foo"
    assert test.description == "test foo"


def test_load_parametrized_test_csv_like_custom_naming_with_format():
    @lcc.suite("suite")
    class MySuite:
        @lcc.test("test")
        @lcc.parametrized(("value", ("foo",)), ("test_{value}", "test {value}"))
        def test(self, value):
            pass

    suite = load_suite_from_class(MySuite)
    test = suite.get_tests()[0]

    assert test.name == "test_foo"
    assert test.description == "test foo"


def test_hidden_test():
    @lcc.suite("My Suite")
    class MySuite:
        @lcc.test("My Test")
        @lcc.hidden()
        def mytest(self):
            pass

    suites = load_suites_from_classes([MySuite])

    assert len(suites[0].get_tests()) == 0


def test_load_suite_from_class_with_hooks():
    @lcc.suite("mysuite")
    class Suite:
        def setup_suite(self):
            return 1

        def teardown_suite(self):
            return 2

        def setup_test(self, test):
            return 3

        def teardown_test(self, test, status):
            return 4

        @lcc.test("some test")
        def sometest(self):
            pass

    suite = load_suite_from_class(Suite)
    assert suite.has_hook("setup_suite")
    assert suite.has_hook("teardown_suite")
    assert suite.has_hook("setup_test")
    assert suite.has_hook("teardown_test")


def test_load_suite_from_class_with_fixture_dependencies():
    @lcc.suite("mysuite")
    class Suite:
        foo = lcc.inject_fixture()

    suite = load_suite_from_class(Suite)
    fixture_names = suite.get_fixtures()
    assert fixture_names == ["foo"]


def test_load_suite_from_file_with_single_suite(tmpdir):
    file = tmpdir.join("my_suite.py")
    file.write(
        """import lemoncheesecake.api as lcc

@lcc.suite()
class my_suite:
    @lcc.test()
    def my_test(self):
        pass
""")

    suite = load_suite_from_file(file.strpath)

    assert suite.name == "my_suite"
    assert len(suite.get_tests()) == 1


def test_load_suite_from_file_without_suite_marker(tmpdir):
    file = tmpdir.join("my_suite.py")
    file.write(
        """import lemoncheesecake.api as lcc

@lcc.test()
def my_test(self):
    pass
""")

    suite = load_suite_from_file(file.strpath)

    assert suite.name == "my_suite"
    assert len(suite.get_tests()) == 1


def test_load_suite_from_file_empty_module(tmpdir):
    file = tmpdir.join("my_suite.py")
    file.write("")

    suite = load_suite_from_file(file.strpath)

    assert suite.name == "my_suite"
    assert suite.description == "My suite"
    assert len(suite.get_tests()) == 0


def test_load_suite_from_file_tests_order(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """
import lemoncheesecake.api as lcc


SUITE = {
    "description": "My Suite"
}


@lcc.test("a")
def a():
    pass


@lcc.test("d")
def d():
    pass


@lcc.test("c")
def c():
    pass


@lcc.test("b")
def b():
    pass
""")

    suite = load_suite_from_file(file.strpath)
    tests = suite.get_tests()

    assert tests[0].name == "a"
    assert tests[1].name == "d"
    assert tests[2].name == "c"
    assert tests[3].name == "b"


def test_load_suite_from_file_suites_order(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """
import lemoncheesecake.api as lcc


SUITE = {
    "description": "My Suite"
}


@lcc.suite("a")
class a:
    @lcc.test("test")
    def test(self):
        pass


@lcc.suite("d")
class d:
    @lcc.test("test")
    def test(self):
        pass


@lcc.suite("c")
class c:
    @lcc.test("test")
    def test(self):
        pass


@lcc.suite("b")
class b:
    @lcc.test("test")
    def test(self):
        pass
""")

    suite = load_suite_from_file(file.strpath)
    suites = suite.get_suites()

    assert suites[0].name == "a"
    assert suites[1].name == "d"
    assert suites[2].name == "c"
    assert suites[3].name == "b"


def test_load_suite_from_file_with_fixture_dependencies(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """import lemoncheesecake.api as lcc

SUITE = {
    "description": "My Suite"
}

foo = lcc.inject_fixture()
""")

    suite = load_suite_from_file(file.strpath)
    fixture_names = suite.get_fixtures()
    assert fixture_names == ["foo"]


def test_load_suite_from_file_with_all_metadata(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """SUITE = {
    "name": "my_suite",
    "description": "My Suite",
    "tags": ["foo", "bar"],
    "properties": {"bar": "baz"},
    "links": [("http://u.r.l/1234", None), ("http://u.r.l/1235", "#1235"), "http://u.r.l/1236"],
}
""")
    suite = load_suite_from_file(file.strpath)
    assert suite.name == "my_suite"
    assert suite.description == "My Suite"
    assert suite.tags == ["foo", "bar"]
    assert suite.properties == {"bar": "baz"}
    assert suite.links == [("http://u.r.l/1234", None), ("http://u.r.l/1235", "#1235"), ("http://u.r.l/1236", None)]


def test_load_suite_from_file_with_test_function(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """import lemoncheesecake.api as lcc

SUITE = {
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


def test_load_suite_from_files_with_condition_on_suite_met(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """import lemoncheesecake.api as lcc
import sys

SUITE = {
    "description": "My Suite",
    "visible_if": lambda mod: mod == sys.modules[__name__]
}

@lcc.test('My Test')
def mytest():
    pass
""")
    suites = load_suites_from_files([file.strpath])
    assert len(suites) == 1


def test_load_suite_from_files_with_condition_on_suite_not_met(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """import lemoncheesecake.api as lcc
import sys

SUITE = {
    "description": "My Suite",
    "visible_if": lambda mod: mod != sys.modules[__name__]
}

@lcc.test('My Test')
def mytest():
    pass
""")
    suites = load_suites_from_files([file.strpath])
    assert len(suites) == 0


def test_load_suite_from_files_with_condition_on_test_met(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """import lemoncheesecake.api as lcc

SUITE = {
    "description": "My Suite",
}

@lcc.test('My Test')
@lcc.visible_if(lambda test_arg: test_arg == mytest)
def mytest():
    pass
""")
    suites = load_suites_from_files([file.strpath])
    assert len(suites[0].get_tests()) == 1


def test_load_suite_from_module_with_condition_on_test_not_met(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """import lemoncheesecake.api as lcc

SUITE = {
    "description": "My Suite",
}

@lcc.test('My Test')
@lcc.visible_if(lambda test_arg: test_arg != mytest)
def mytest():
    pass
""")
    suites = load_suites_from_files([file.strpath])
    assert len(suites) == 0


def test_load_suite_from_file_with_test_function_and_fixtures(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """import lemoncheesecake.api as lcc

SUITE = {
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
    assert test.get_fixtures() == ["fixt1", "fixt2"]


def test_load_suite_from_file_with_sub_suite(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """import lemoncheesecake.api as lcc

SUITE = {
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


def test_load_suite_from_file_with_hooks(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """import lemoncheesecake.api as lcc

SUITE = {
    "description": "My Suite"
}

def setup_suite():
    return 1

def teardown_suite():
    return 2

def setup_test(test):
    return 3

def teardown_test(test, status):
    return 4

@lcc.test('My Test')
def mytest():
    pass
""")
    suite = load_suite_from_file(file.strpath)
    assert suite.has_hook("setup_suite")
    assert suite.has_hook("teardown_suite")
    assert suite.has_hook("setup_test")
    assert suite.has_hook("teardown_test")


def test_load_suites_from_directory_with_suite_and_sub_suite(tmpdir):
    tmpdir.join("mysuite.py").write(
        """import lemoncheesecake.api as lcc

SUITE = {
    "description": "My Suite"
}

@lcc.test('My Test')
def mytest1():
    pass
""")

    tmpdir.mkdir("mysuite").join("subsuite.py").write(
        """import lemoncheesecake.api as lcc

SUITE = {
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


def test_load_suite_class_with_property():
    @lcc.suite("mysuite")
    class mysuite(object):
        @lcc.test("mytest")
        def mytest(self):
            pass

        @property
        def myprop(self):
            # ensure that myprop is not called:
            assert False

    suite = load_suite_from_class(mysuite)
    assert len(suite.get_tests()) == 1


def test_invalid_type_name():
    @lcc.test("test", name=1)
    def test():
        pass

    with pytest.raises(SuiteLoadingError, match="Invalid test metadata"):
        _load_test(test)


def test_invalid_type_description():
    @lcc.test(1)
    def test():
        pass

    with pytest.raises(SuiteLoadingError, match="Invalid test metadata"):
        _load_test(test)


def test_invalid_type_tag():
    @lcc.test("test")
    @lcc.tags(1)
    def test():
        pass

    with pytest.raises(SuiteLoadingError, match="Invalid test metadata"):
        _load_test(test)


def test_invalid_type_link_url():
    @lcc.test("test")
    @lcc.link(1)
    def test():
        pass

    with pytest.raises(SuiteLoadingError, match="Invalid test metadata"):
        _load_test(test)


def test_invalid_type_link_name():
    @lcc.test("test")
    @lcc.link("http://www.example.com", 1)
    def test():
        pass

    with pytest.raises(SuiteLoadingError, match="Invalid test metadata"):
        _load_test(test)


def test_invalid_type_prop():
    @lcc.test("test")
    @lcc.prop("foo", 1)
    def test():
        pass

    with pytest.raises(SuiteLoadingError, match="Invalid test metadata"):
        _load_test(test)


def test_invalid_type_on_suite_class():
    @lcc.suite("suite")
    @lcc.prop("foo", 1)
    class suite():
        pass

    with pytest.raises(SuiteLoadingError, match="Invalid suite metadata"):
        load_suite_from_class(suite)


def test_invalid_type_on_suite_module(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(
        """SUITE = {
    "description": "My Suite",
    "tags": [1]
}
""")

    with pytest.raises(SuiteLoadingError, match="Invalid suite metadata"):
        load_suite_from_file(file.strpath)
