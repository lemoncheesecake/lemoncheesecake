import os.path

import pytest

import lemoncheesecake as lcc
from lemoncheesecake.testsuite.loader import load_testsuites_from_directory, load_testsuite_from_file, load_testsuite_from_class, load_testsuites_from_files, load_testsuites_from_classes
from lemoncheesecake.validators import MetadataPolicy
from lemoncheesecake.exceptions import *
from helpers import build_test_module

def test_load_testsuite_from_file(tmpdir):
    file = tmpdir.join("mytestsuite.py")
    file.write(build_test_module())
    klass = load_testsuite_from_file(file.strpath)
    assert klass.name == "mytestsuite"

def test_load_testsuite_from_file_invalid_module(tmpdir):
    file = tmpdir.join("doesnotexist.py")
    with pytest.raises(ImportTestSuiteError):
        load_testsuite_from_file(file.strpath)

def test_load_testsuite_from_file_invalid_class(tmpdir):
    file = tmpdir.join("anothertestsuite.py")
    file.write(build_test_module())
    with pytest.raises(ImportTestSuiteError):
        load_testsuite_from_file(file.strpath)

def test_load_testsuites_from_directory_without_modules(tmpdir):
    klasses = load_testsuites_from_directory(tmpdir.strpath)
    assert len(klasses) == 0

def test_load_testsuites_from_directory_with_modules(tmpdir):
    names = []
    for i in range(3):
        name = "mytestsuite%d" % i
        names.append(name)
        tmpdir.join("%s.py" % name).write(build_test_module(name))
    klasses = load_testsuites_from_directory(tmpdir.strpath)
    for name in names:
        assert name in [k.name for k in klasses]

def test_load_testsuites_from_directory_with_subdir(tmpdir):
    file = tmpdir.join("parentsuite.py")
    file.write(build_test_module("parentsuite"))
    subdir = tmpdir.join("parentsuite")
    subdir.mkdir()
    file = subdir.join("childsuite.py")
    file.write(build_test_module("childsuite"))
    klasses = load_testsuites_from_directory(tmpdir.strpath)
    assert klasses[0].name == "parentsuite"
    assert len(klasses[0].get_sub_testsuites()) == 1

def test_load_testsuites_from_files(tmpdir):
    for name in "testsuite1", "testsuite2", "mysuite":
        tmpdir.join(name + ".py").write(build_test_module(name))
    klasses = load_testsuites_from_files(tmpdir.join("testsuite*.py").strpath)
    assert len(klasses) == 2
    assert "testsuite1" in [k.name for k in klasses]
    assert "testsuite2" in [k.name for k in klasses]

def test_load_testsuites_from_files_nomatch(tmpdir):
    klasses = load_testsuites_from_files(tmpdir.join("*.py").strpath)
    assert len(klasses) == 0

def test_load_testsuites_from_files_exclude(tmpdir):
    for name in "testsuite1", "testsuite2", "mysuite":
        tmpdir.join(name + ".py").write(build_test_module(name))
    klasses = load_testsuites_from_files(tmpdir.join("*.py").strpath, "*/testsuite*.py")
    assert len(klasses) == 1
    assert klasses[0].name == "mysuite"

def test_load_suites_with_same_name():
    @lcc.testsuite("My Suite 1")
    class MySuite1:
        @lcc.testsuite("My Sub Suite 1")
        class MySubSuite:
            @lcc.test("foo")
            def foo(self):
                pass
    
    @lcc.testsuite("My Suite 2")
    class MySuite2:
        @lcc.testsuite("My Sub Suite 1")
        class MySubSuite:
            @lcc.test("bar")
            def bar(self):
                pass
    
    suites = load_testsuites_from_classes([MySuite1, MySuite2])
    
    assert suites[0].get_suite_name() == "MySuite1"
    assert suites[0].get_sub_testsuites()[0].get_suite_name() == "MySubSuite"
    assert suites[1].get_suite_name() == "MySuite2"
    assert suites[1].get_sub_testsuites()[0].get_suite_name() == "MySubSuite"

def test_load_tests_with_same_name():
    @lcc.testsuite("My Suite 1")
    class MySuite1:
        @lcc.testsuite("My Sub Suite 1")
        class MySubSuite1:
            @lcc.test("foo")
            def foo(self):
                pass

    @lcc.testsuite("My Suite 2")
    class MySuite2:
        @lcc.testsuite("My Sub Suite 2")
        class MySubSuite2:
            @lcc.test("foo")
            def foo(self):
                pass
    
    suites = load_testsuites_from_classes([MySuite1, MySuite2])
    
    assert suites[0].get_suite_name() == "MySuite1"
    assert suites[0].get_sub_testsuites()[0].get_suite_name() == "MySubSuite1"
    assert suites[0].get_sub_testsuites()[0].get_tests()[0].name == "foo"
    assert suites[1].get_suite_name() == "MySuite2"
    assert suites[1].get_sub_testsuites()[0].get_suite_name() == "MySubSuite2"
    assert suites[1].get_sub_testsuites()[0].get_tests()[0].name == "foo"

def test_metadata_policy():
    @lcc.testsuite("My Suite 1")
    class MySuite1:
        @lcc.prop("foo", 3)
        @lcc.test("Some test")
        def sometest(self):
            pass
        
    @lcc.testsuite("My Suite 1")
    @lcc.prop("foo", 3)
    class MySuite2:
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    suite1 = load_testsuites_from_classes([MySuite1])
    suite2 = load_testsuites_from_classes([MySuite2])
    
    policy = MetadataPolicy()
    policy.add_property_rule("foo", (1, 2))
    with pytest.raises(InvalidMetadataError):
        policy.check_suites_compliance(suite1)
    with pytest.raises(InvalidMetadataError):
        policy.check_suites_compliance(suite2)
