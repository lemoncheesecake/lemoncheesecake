import re

from lemoncheesecake.cli import main
from lemoncheesecake.cli.commands.top import TopSuites, TopTests, TopSteps
from lemoncheesecake.reporting.backends.json_ import save_report_into_file
from lemoncheesecake.filter import ResultFilter, StepFilter
import lemoncheesecake.api as lcc

from helpers.cli import cmdout
from helpers.report import report_in_progress_path
from helpers.runner import run_suite_class
from helpers.report import make_test_result, make_suite_result, make_step, make_report


def test_get_top_suites():
    report = make_report([
        make_suite_result("suite1", tests=[make_test_result("test", start_time=0.0, end_time=1.0)]),
        make_suite_result("suite2", tests=[make_test_result("test", start_time=1.0, end_time=4.0)]),
    ])

    top_suites = TopSuites.get_top_suites(report, ResultFilter())
    assert len(top_suites) == 2
    assert top_suites[0][0] == "suite2"
    assert top_suites[0][1] == 1
    assert top_suites[0][2] == "3.000s"
    assert top_suites[0][3] == "75%"
    assert top_suites[1][0] == "suite1"
    assert top_suites[1][1] == 1
    assert top_suites[1][2] == "1.000s"
    assert top_suites[1][3] == "25%"


def test_get_top_suites_with_suite_setup():
    @lcc.suite("suite")
    class suite:
        def setup_suite(self):
            lcc.log_info("foobar")

        @lcc.test("test")
        def test(self):
            pass

    report = run_suite_class(suite)

    top_suites = TopSuites.get_top_suites(report, ResultFilter(grep=re.compile("foobar")))

    assert len(top_suites) == 1

    assert top_suites[0][0] == "suite"
    assert top_suites[0][1] == 0
    assert top_suites[0][3] == "100%"


def test_top_suites_cmd(tmpdir, cmdout):
    report = make_report([
        make_suite_result("suite1", tests=[make_test_result("test", start_time=0.1, end_time=1.0)]),
        make_suite_result("suite2", tests=[make_test_result("test", start_time=1.0, end_time=4.0)]),
    ])

    report_path = tmpdir.join("report.json").strpath
    save_report_into_file(report, report_path)

    assert main(["top-suites", report_path]) == 0

    lines = cmdout.get_lines()
    assert "suite2" in lines[4]


def test_top_suites_cmd_test_run_in_progress(report_in_progress_path, cmdout):
    assert main(["top-suites", report_in_progress_path]) == 0

    cmdout.dump()
    cmdout.assert_substrs_anywhere(["suite"])


def test_get_top_tests():
    report = make_report([
        make_suite_result("suite1", tests=[make_test_result("test", start_time=0.0, end_time=1.0)]),
        make_suite_result("suite2", tests=[make_test_result("test", start_time=1.0, end_time=4.0)]),
    ])

    top_suites = TopTests.get_top_tests(report, ResultFilter())
    assert len(top_suites) == 2
    assert top_suites[0][0] == "suite2.test"
    assert top_suites[0][1] == "3.000s"
    assert top_suites[0][2] == "75%"
    assert top_suites[1][0] == "suite1.test"
    assert top_suites[1][1] == "1.000s"
    assert top_suites[1][2] == "25%"


def test_top_tests_cmd(tmpdir, cmdout):
    report = make_report([
        make_suite_result("suite1", tests=[make_test_result("test", start_time=0.1, end_time=1.0)]),
        make_suite_result("suite2", tests=[make_test_result("test", start_time=1.0, end_time=4.0)]),
    ])

    report_path = tmpdir.join("report.json").strpath
    save_report_into_file(report, report_path)

    assert main(["top-tests", report_path]) == 0

    lines = cmdout.get_lines()
    assert "suite2.test" in lines[4]


def test_top_tests_cmd_test_run_in_progress(report_in_progress_path, cmdout):
    assert main(["top-tests", report_in_progress_path]) == 0

    cmdout.dump()
    cmdout.assert_substrs_anywhere(["suite.test_2"])


def test_get_top_steps():
    report = make_report([
        make_suite_result("suite1", tests=[make_test_result(steps=[
            make_step("step1", start_time=0.0, end_time=1.0),
            make_step("step1", start_time=1.0, end_time=3.0),
        ])]),
        make_suite_result("suite2", tests=[make_test_result(steps=[
            make_step("step2", start_time=3.0, end_time=4.0)
        ])]),
    ])

    top_steps = TopSteps.get_top_steps(report, StepFilter())

    assert len(top_steps) == 2

    assert top_steps[0][0] == "step1"
    assert top_steps[0][1] == "2"
    assert top_steps[0][2] == "1.000s"
    assert top_steps[0][3] == "2.000s"
    assert top_steps[0][4] == "1.500s"
    assert top_steps[0][5] == "3.000s"
    assert top_steps[0][6] == "75%"

    assert top_steps[1][0] == "step2"
    assert top_steps[1][1] == "1"
    assert top_steps[1][2] == "1.000s"
    assert top_steps[1][3] == "1.000s"
    assert top_steps[1][4] == "1.000s"
    assert top_steps[1][5] == "1.000s"
    assert top_steps[1][6] == "25%"


def test_get_top_steps_with_test_session_setup_and_grep():
    @lcc.fixture(scope="session")
    def fixt():
        lcc.set_step("mystep")
        lcc.log_info("foobar")

    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self, fixt):
            pass

    report = run_suite_class(suite, fixtures=[fixt])

    top_steps = TopSteps.get_top_steps(report, StepFilter(grep=re.compile("foobar")))

    assert len(top_steps) == 1
    assert top_steps[0][0] == "mystep"


def test_get_top_steps_filter_on_passed():
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.set_step("something ok")
            lcc.log_info("info")
            lcc.set_step("something not ok")
            lcc.log_error("error")

    report = run_suite_class(suite)

    top_steps = TopSteps.get_top_steps(report, StepFilter(passed=True))

    assert len(top_steps) == 1
    assert top_steps[0][0] == "something ok"


def test_get_top_steps_filter_on_grep():
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.set_step("something ok")
            lcc.log_info("info")
            lcc.set_step("something not ok")
            lcc.log_error("error")

    report = run_suite_class(suite)

    top_steps = TopSteps.get_top_steps(report, StepFilter(grep=re.compile("error")))

    assert len(top_steps) == 1
    assert top_steps[0][0] == "something not ok"


def test_top_steps_cmd(tmpdir, cmdout):
    report = make_report([
        make_suite_result("suite1", tests=[
            make_test_result(steps=[make_step("step1", start_time=0.1, end_time=1.0)])
        ])
    ])

    report_path = tmpdir.join("report.json").strpath
    save_report_into_file(report, report_path)

    assert main(["top-steps", report_path]) == 0

    lines = cmdout.get_lines()
    assert "step1" in lines[4]


def test_top_steps_cmd_test_run_in_progress(report_in_progress_path, cmdout):
    assert main(["top-steps", report_in_progress_path]) == 0

    cmdout.dump()
    cmdout.assert_substrs_anywhere(["step"])
