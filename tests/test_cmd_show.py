import os
import pytest

from helpers import generate_project, cmdout

from lemoncheesecake.cli import main

TEST_MODULE = """import lemoncheesecake as lcc

@lcc.testsuite("My Suite")
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
    main(["show"])
    
    cmdout.assert_substrs_in_line(0, ["mysuite", "suite_prop", "suite_prop_value", "suite_tag", "#1234"])
    cmdout.assert_substrs_in_line(1, ["mysuite.mytest", "test_prop", "test_prop_value", "test_tag", "#1235"])

def test_show_opt_short(project, cmdout):
    main(["show", "--short"])

    cmdout.assert_substrs_in_line(0, ["mysuite", "suite_prop", "suite_prop_value", "suite_tag", "#1234"])
    cmdout.assert_substrs_in_line(1, ["mytest", "test_prop", "test_prop_value", "test_tag", "#1235"])

def test_show_opt_flat_mode(project, cmdout):
    # also add --no-color to make the startswith on suite easier
    main(["show", "--flat-mode", "--no-color"])

    cmdout.assert_line_startswith(0, "mysuite")
    cmdout.assert_substrs_in_line(0, ["suite_prop", "suite_prop_value", "suite_tag", "#1234"])
    cmdout.assert_line_startswith(1, "mysuite.mytest")
    cmdout.assert_substrs_in_line(1, ["test_prop", "test_prop_value", "test_tag", "#1235"])

def test_show_opt_desc_mode(project, cmdout):
    main(["show", "--desc-mode"])

    cmdout.assert_substrs_in_line(0, ["My Suite", "suite_prop", "suite_prop_value", "suite_tag", "#1234"])
    cmdout.assert_substrs_in_line(1, ["My Test", "test_prop", "test_prop_value", "test_tag", "#1235"])

def test_show_opt_no_metadata(project, cmdout):
    main(["show", "--no-metadata"])

    cmdout.assert_substrs_in_line(0, ["mysuite"])
    cmdout.assert_substrs_not_in_line(0, ["suite_prop", "suite_prop_value", "suite_tag", "#1234"])
    cmdout.assert_substrs_in_line(1, ["mysuite.mytest"])
    cmdout.assert_substrs_not_in_line(1, ["test_prop", "test_prop_value", "test_tag", "#1235"])

def test_show_with_filter(project, cmdout):
    main(["show", "--tag", "doesnotexist"])
    
    cmdout.assert_lines_nb(0)
    cmdout.assert_lines_nb(0, on_stderr=True)