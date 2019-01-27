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
    @lcc.test("My Test")
    @lcc.prop("test_prop", "test_prop_value")
    @lcc.tags("test_tag")
    @lcc.link("http://bug.tra.cker/1235", "#1235")
    def mytest(self):
        pass
"""


@pytest.fixture()
def project(tmpdir):
    generate_project(tmpdir.strpath, "mysuite", TEST_MODULE)
    old_cwd = os.getcwd()
    os.chdir(tmpdir.strpath)
    yield
    os.chdir(old_cwd)


def test_show_default_options(project, cmdout):
    assert run_main(["show"]) == 0
    
    cmdout.assert_substrs_in_line(0, ["mysuite", "suite_prop", "suite_prop_value", "suite_tag", "#1234"])
    cmdout.assert_substrs_in_line(1, ["mysuite.mytest", "test_prop", "test_prop_value", "test_tag", "#1235"])


def test_show_opt_show_description(project, cmdout):
    assert run_main(["show", "--show-description"]) == 0

    cmdout.assert_substrs_in_line(0, ["My Suite", "suite_prop", "suite_prop_value", "suite_tag", "#1234"])
    cmdout.assert_substrs_in_line(1, ["My Test", "test_prop", "test_prop_value", "test_tag", "#1235"])


def test_show_with_filter(project, cmdout):
    assert "does not match" in run_main(["show", "--tag", "doesnotexist"])
