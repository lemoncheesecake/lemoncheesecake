import os
import pytest

from helpers.runner import generate_project, run_main
from helpers.cli import cmdout

FIXTURES_MODULE = """import lemoncheesecake.api as lcc

@lcc.fixture(scope="pre_run")
def qux():
    pass

@lcc.fixture(scope="session")
def foo(qux):
    pass

@lcc.fixture(scope="suite")
def bar(foo):
    pass


@lcc.fixture(scope="test")
def baz(bar):
    pass
"""

TEST_MODULE = """import lemoncheesecake.api as lcc

@lcc.suite("My Suite")
class mysuite:
    @lcc.test("My Test 1")
    def mytest1(self, foo, bar, baz):
        pass

    @lcc.test("My Test 2")
    def mytest2(self, foo, baz):
        pass

"""

EMPTY_TEST_MODULE = """import lemoncheesecake.api as lcc

@lcc.suite("My Suite")
class mysuite:
    pass
"""


@pytest.fixture()
def project(tmpdir):
    generate_project(tmpdir.strpath, "mysuite", TEST_MODULE, FIXTURES_MODULE)
    old_cwd = os.getcwd()
    os.chdir(tmpdir.strpath)
    yield
    os.chdir(old_cwd)


@pytest.fixture()
def notest_project(tmpdir):
    generate_project(tmpdir.strpath, "mysuite", EMPTY_TEST_MODULE)
    old_cwd = os.getcwd()
    os.chdir(tmpdir.strpath)
    yield
    os.chdir(old_cwd)


def test_fixtures(project, cmdout):
    assert run_main(["fixtures"]) == 0

    cmdout.assert_lines_match(".+qux.+ 1 .+ 0 .+")
    cmdout.assert_lines_match(".+foo.+ 1 .+ 2 .+")
    cmdout.assert_lines_match(".+bar.+foo.+ 1 .+ 1 .+")
    cmdout.assert_lines_match(".+baz.+bar.+ 0 .+ 2 .+")


def test_fixtures_empty_project(notest_project, cmdout):
    assert run_main(["fixtures"]) == 0

    cmdout.assert_lines_match(".*pre_run.*:.*none.*")
    cmdout.assert_lines_match(".*session.*:.*none.*")
    cmdout.assert_lines_match(".*suite.*:.*none.*")
    cmdout.assert_lines_match(".*test.*:.*none.*")
