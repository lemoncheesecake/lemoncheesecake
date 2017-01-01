import os.path

import pytest

import lemoncheesecake as lcc
from lemoncheesecake import loader
from lemoncheesecake.launcher.validators import MetadataPolicy
from lemoncheesecake.exceptions import *
from helpers import build_test_module

def test_import_testsuite_from_file(tmpdir):
    file = tmpdir.join("mytestsuite.py")
    file.write(build_test_module())
    klass = loader.import_testsuite_from_file(file.strpath)
    assert klass.__name__ == "mytestsuite"

def test_import_testsuite_from_file_invalid_module(tmpdir):
    file = tmpdir.join("doesnotexist.py")
    with pytest.raises(ImportTestSuiteError):
        loader.import_testsuite_from_file(file.strpath)

def test_import_testsuite_from_file_invalid_class(tmpdir):
    file = tmpdir.join("anothertestsuite.py")
    file.write(build_test_module())
    with pytest.raises(ImportTestSuiteError):
        loader.import_testsuite_from_file(file.strpath)

def test_import_testsuites_from_directory_without_modules(tmpdir):
    klasses = loader.import_testsuites_from_directory(tmpdir.strpath)
    assert len(klasses) == 0

def test_import_testsuites_from_directory_with_modules(tmpdir):
    names = []
    for i in range(3):
        name = "mytestsuite%d" % i
        names.append(name)
        tmpdir.join("%s.py" % name).write(build_test_module(name))
    klasses = loader.import_testsuites_from_directory(tmpdir.strpath)
    for name in names:
        assert name in [k.__name__ for k in klasses]

def test_import_testsuites_from_directory_with_subdir(tmpdir):
    file = tmpdir.join("parentsuite.py")
    file.write(build_test_module("parentsuite"))
    subdir = tmpdir.join("parentsuite")
    subdir.mkdir()
    file = subdir.join("childsuite.py")
    file.write(build_test_module("childsuite"))
    klasses = loader.import_testsuites_from_directory(tmpdir.strpath)
    assert klasses[0].__name__ == "parentsuite"
    assert len(klasses[0].sub_suites) == 1

def test_import_testsuites_from_files(tmpdir):
    for name in "testsuite1", "testsuite2", "mysuite":
        tmpdir.join(name + ".py").write(build_test_module(name))
    klasses = loader.import_testsuites_from_files(tmpdir.join("testsuite*.py").strpath)
    assert len(klasses) == 2
    assert "testsuite1" in [k.__name__ for k in klasses]
    assert "testsuite2" in [k.__name__ for k in klasses]

def test_import_testsuites_from_files_nomatch(tmpdir):
    klasses = loader.import_testsuites_from_files(tmpdir.join("*.py").strpath)
    assert len(klasses) == 0

def test_import_testsuites_from_files_exclude(tmpdir):
    for name in "testsuite1", "testsuite2", "mysuite":
        tmpdir.join(name + ".py").write(build_test_module(name))
    klasses = loader.import_testsuites_from_files(tmpdir.join("*.py").strpath, "*/testsuite*.py")
    assert len(klasses) == 1
    assert klasses[0].__name__ == "mysuite"

def test_metadata_policy():
    class MySuite1(lcc.TestSuite):
        @lcc.prop("foo", 3)
        @lcc.test("Some test")
        def sometest(self):
            pass
        
    @lcc.prop("foo", 3)
    class MySuite2(lcc.TestSuite):
        @lcc.test("Some test")
        def sometest(self):
            pass
    
    policy = MetadataPolicy()
    policy.add_property_rule("foo", (1, 2))
    with pytest.raises(InvalidMetadataError):
        loader.load_testsuites([MySuite1], policy)
    with pytest.raises(InvalidMetadataError):
        loader.load_testsuites([MySuite2], policy)
