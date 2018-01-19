import os
import pytest

from helpers.runner import generate_project, run_main
from helpers.cli import cmdout


TEST_MODULE = """import lemoncheesecake.api as lcc

@lcc.suite("My Suite")
@lcc.prop("suite_prop", "suite_prop_value")
@lcc.tags("suite_tag")
@lcc.link("http://bug.tra.cker/1234", "#1234")
class mysuite:
    @lcc.test("My Test 1")
    @lcc.prop("test_prop", "test_prop_value1")
    @lcc.tags("test_tag", "suite_tag")
    @lcc.link("http://bug.tra.cker/1234", "#1234")
    def mytest1(self):
        pass

    @lcc.test("My Test 2")
    @lcc.prop("test_prop", "test_prop_value2")
    @lcc.tags("foo")
    @lcc.link("http://bug.tra.cker/1235")
    def mytest2(self):
        pass

"""

EMPTY_TEST_MODULE = """import lemoncheesecake.api as lcc

@lcc.suite("My Suite")
class mysuite:
    pass
"""


@pytest.fixture()
def project(tmpdir):
    generate_project(tmpdir.strpath, "mysuite", TEST_MODULE)
    old_cwd = os.getcwd()
    os.chdir(tmpdir.strpath)
    yield
    os.chdir(old_cwd)


@pytest.fixture()
def empty_project(tmpdir):
    generate_project(tmpdir.strpath, "mysuite", EMPTY_TEST_MODULE)
    old_cwd = os.getcwd()
    os.chdir(tmpdir.strpath)
    yield
    os.chdir(old_cwd)


def test_stats(project, cmdout):
    assert run_main(["stats"]) == 0

    # tags:
    cmdout.assert_lines_match(".+suite_tag.+ 2 .+ 100%")
    cmdout.assert_lines_match(".+test_tag.+ 1 .+ 50%")
    cmdout.assert_lines_match(".+foo.+ 1 .+ 50%")

    # properties:
    cmdout.assert_lines_match(".+suite_prop.+suite_prop_value.+ 2 .+ 100%")
    cmdout.assert_lines_match(".+test_prop.+test_prop_value1.+ 1 .+ 50%")
    cmdout.assert_lines_match(".+test_prop.+test_prop_value2.+ 1 .+ 50%")

    # links:
    cmdout.assert_lines_match(".+#1234.+http://bug.tra.cker/1234.+ 2 .+ 100%")
    cmdout.assert_lines_match(".+-.+http://bug.tra.cker/1235.+ 1 .+ 50%")

    # totals:
    cmdout.assert_lines_match(".+2.+tests.+1.+suites.*")


def test_stats_empty_project(empty_project, cmdout):
    assert "No test is defined" in run_main(["stats"])


def test_stats_with_filter(project, cmdout):
    assert run_main(["stats", "mysuite.mytest1"]) == 0

    # tags:
    cmdout.assert_lines_match(".+suite_tag.+ 1 .+ 100%")
    cmdout.assert_lines_match(".+test_tag.+ 1 .+ 100%")

    # properties:
    cmdout.assert_lines_match(".+suite_prop.+suite_prop_value.+ 1 .+ 100%")
    cmdout.assert_lines_match(".+test_prop.+test_prop_value1.+ 1 .+ 100%")

    # links:
    cmdout.assert_lines_match(".+#1234.+http://bug.tra.cker/1234.+ 1 .+ 100%")

    # totals:
    cmdout.assert_lines_match(".+1.+tests.+1.+suites.*")
