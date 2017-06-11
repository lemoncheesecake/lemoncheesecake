import os
import pytest

from helpers import generate_project, cmdout

from lemoncheesecake.cli import main

TEST_MODULE = """import lemoncheesecake.api as lcc

@lcc.testsuite("My Suite")
class mysuite:
    @lcc.test("My Test 1")
    def mytest1(self):
        lcc.log_error("failure")

    @lcc.test("My Test 2")
    def mytest2(self):
        pass

"""

FIXTURE_MODULE = """import lemoncheesecake.api as lcc
@lcc.fixture()
def fixt():
    return 42
"""

TEST_MODULE_USING_FIXTURES = """import lemoncheesecake.api as lcc

@lcc.testsuite("My Suite")
class mysuite:
    @lcc.test("My Test 1")
    def mytest1(self, fixt):
        lcc.check_that("val", fixt, lcc.equal_to(42))
"""


@pytest.fixture()
def project(tmpdir):
    generate_project(tmpdir.strpath, "mysuite", TEST_MODULE)
    old_cwd = os.getcwd()
    os.chdir(tmpdir.strpath)
    yield
    os.chdir(old_cwd)

@pytest.fixture()
def project_with_fixtures(tmpdir):
    generate_project(tmpdir.strpath, "mysuite", TEST_MODULE_USING_FIXTURES, FIXTURE_MODULE)
    old_cwd = os.getcwd()
    os.chdir(tmpdir.strpath)
    yield
    os.chdir(old_cwd)

def test_run(project, cmdout):
    assert main(["run"]) == 0

    cmdout.assert_lines_match(".+= mysuite =.+")
    cmdout.assert_lines_match(".+KO.+mytest1.+")
    cmdout.assert_lines_match(".+OK.+mytest2.+")
    cmdout.assert_lines_match(".+Tests: 2")
    cmdout.assert_lines_match(".+Successes: 1")
    cmdout.assert_lines_match(".+Failures: 1")

def test_run_with_filter(project, cmdout):
    assert main(["run", "mysuite.mytest1"]) == 0

    cmdout.assert_lines_match(".+= mysuite =.+")
    cmdout.assert_lines_match(".+KO.+mytest1.+")
    cmdout.assert_lines_match(".+Tests: 1")
    cmdout.assert_lines_match(".+Successes: 0")
    cmdout.assert_lines_match(".+Failures: 1")

def test_project_with_fixtures(project_with_fixtures, cmdout):
    assert main(["run", "mysuite.mytest1"]) == 0

    cmdout.assert_lines_match(".+= mysuite =.+")
    cmdout.assert_lines_match(".+OK.+mytest1.+")
    cmdout.assert_lines_match(".+Tests: 1")
    cmdout.assert_lines_match(".+Successes: 1")
    cmdout.assert_lines_match(".+Failures: 0")
