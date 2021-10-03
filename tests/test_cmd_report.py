import os.path as osp

from helpers.runner import run_suite_class
from helpers.cli import assert_run_output, cmdout
from helpers.report import report_in_progress_path

import lemoncheesecake.api as lcc
from lemoncheesecake.cli import main
from lemoncheesecake.reporting.backends.json_ import JsonBackend


@lcc.suite("My suite")
class mysuite:
    @lcc.test("My Test 1")
    def mytest1(self):
        lcc.log_error("failure")

    @lcc.test("My Test 2")
    def mytest2(self):
        pass


@lcc.suite()
class suite_with_debug:
    @lcc.test()
    def test(self):
        lcc.set_step("step 1")
        lcc.log_info("1_info_message")
        lcc.log_debug("1_debug_message")
        lcc.set_step("step 2")
        lcc.log_debug("2_debug_message")

    @lcc.test("My Test 2")
    def mytest2(self):
        pass


def test_report_from_dir(tmpdir, cmdout):
    run_suite_class(mysuite, tmpdir=tmpdir, backends=[JsonBackend()])

    assert main(["report", tmpdir.strpath, "--short"]) == 0
    assert_run_output(cmdout, "mysuite", successful_tests=["mytest2"], failed_tests=["mytest1"])


def test_report_from_file(tmpdir, cmdout):
    backend = JsonBackend()
    run_suite_class(mysuite, tmpdir=tmpdir, backends=[backend])

    assert main(["report", osp.join(tmpdir.strpath, backend.get_report_filename()), "--short"]) == 0
    assert_run_output(cmdout, "mysuite", successful_tests=["mytest2"], failed_tests=["mytest1"])


def test_report_with_filter(tmpdir, cmdout):
    run_suite_class(mysuite, tmpdir=tmpdir, backends=[JsonBackend()])

    assert main(["report", tmpdir.strpath, "--passed", "--short"]) == 0
    assert_run_output(cmdout, "mysuite", successful_tests=["mytest2"])


def test_report_detailed(tmpdir, cmdout):
    run_suite_class(mysuite, tmpdir=tmpdir, backends=[JsonBackend()])

    assert main(["report", tmpdir.strpath]) == 0

    cmdout.dump()
    cmdout.assert_substrs_in_line(0, ["My Test 1"])
    cmdout.assert_substrs_in_line(1, ["mysuite.mytest1"])
    cmdout.assert_substrs_in_line(3, ["My Test 1"])
    cmdout.assert_substrs_in_line(5, ["ERROR", "failure"])
    cmdout.assert_substrs_in_line(8, ["My Test 2"])
    cmdout.assert_substrs_in_line(9, ["mysuite.mytest2"])
    cmdout.assert_substrs_in_line(10, ["n/a"])
    cmdout.assert_lines_nb(13)


def test_report_detailed_with_arguments(tmpdir, cmdout):
    run_suite_class(mysuite, tmpdir=tmpdir, backends=[JsonBackend()])

    assert main(["report", tmpdir.strpath, "--explicit", "--max-width=80"]) == 0

    cmdout.dump()
    cmdout.assert_substrs_in_line(0, ["FAILED: My Test 1"])
    cmdout.assert_substrs_in_line(1, ["mysuite.mytest1"])
    cmdout.assert_substrs_in_line(3, ["My Test 1"])
    cmdout.assert_substrs_in_line(5, ["ERROR", "failure"])
    cmdout.assert_substrs_in_line(8, ["My Test 2"])
    cmdout.assert_substrs_in_line(9, ["mysuite.mytest2"])
    cmdout.assert_substrs_in_line(10, ["n/a"])
    cmdout.assert_lines_nb(13)


def test_report_detailed_with_filter(tmpdir, cmdout):
    run_suite_class(mysuite, tmpdir=tmpdir, backends=[JsonBackend()])

    assert main(["report", tmpdir.strpath, "--failed"]) == 0

    cmdout.dump()
    cmdout.assert_substrs_in_line(0, ["My Test 1"])
    cmdout.assert_substrs_in_line(1, ["mysuite.mytest1"])
    cmdout.assert_substrs_in_line(3, ["My Test 1"])
    cmdout.assert_substrs_in_line(5, ["ERROR", "failure"])
    cmdout.assert_lines_nb(9)


def test_report_detailed_with_filter_grep(tmpdir, cmdout):
    run_suite_class(mysuite, tmpdir=tmpdir, backends=[JsonBackend()])

    assert main(["report", tmpdir.strpath, "--grep", "failure"]) == 0

    cmdout.dump()
    cmdout.assert_substrs_in_line(0, ["My Test 1"])
    cmdout.assert_substrs_in_line(1, ["mysuite.mytest1"])
    cmdout.assert_substrs_in_line(3, ["My Test 1"])
    cmdout.assert_substrs_in_line(5, ["ERROR", "failure"])
    cmdout.assert_lines_nb(9)


def test_report_test_run_in_progress(report_in_progress_path, cmdout):
    assert main(["report", report_in_progress_path]) == 0

    cmdout.dump()
    cmdout.assert_substrs_anywhere(["suite.test_1"])
    cmdout.assert_substrs_anywhere(["step"])
    cmdout.assert_substrs_anywhere(["message"])


def test_report_without_debug_arg(tmpdir, cmdout):
    run_suite_class(suite_with_debug, tmpdir=tmpdir, backends=[JsonBackend()])

    assert main(["report", tmpdir.strpath]) == 0

    cmdout.dump()

    cmdout.assert_substrs_anywhere(["step 1"])
    cmdout.assert_substrs_anywhere(["1_info_message"])
    cmdout.assert_substrs_nowhere(["1_debug_message"])
    cmdout.assert_substrs_nowhere(["step 2"])
    cmdout.assert_substrs_nowhere(["2_debug_message"])


def test_report_with_debug_arg(tmpdir, cmdout):
    run_suite_class(suite_with_debug, tmpdir=tmpdir, backends=[JsonBackend()])

    assert main(["report", tmpdir.strpath, "--debug"]) == 0

    cmdout.dump()

    cmdout.assert_substrs_anywhere(["step 1"])
    cmdout.assert_substrs_anywhere(["1_info_message"])
    cmdout.assert_substrs_anywhere(["1_debug_message"])
    cmdout.assert_substrs_anywhere(["step 2"])
    cmdout.assert_substrs_anywhere(["2_debug_message"])
