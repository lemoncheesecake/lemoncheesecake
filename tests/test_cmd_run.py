import os
import os.path as osp

from unittest.mock import patch

import pytest
from callee import Any, Matcher

import lemoncheesecake.api as lcc
from lemoncheesecake.project import Project
from lemoncheesecake.suite import load_suite_from_class
from lemoncheesecake.cli import build_cli_args
from lemoncheesecake.cli.commands.run import run_suites_from_project
from lemoncheesecake.reporting import savingstrategy
from lemoncheesecake.exceptions import LemoncheesecakeException

from helpers.runner import generate_project, run_main
from helpers.cli import assert_run_output, cmdout
from helpers.utils import change_dir, tmp_cwd, env_vars


TEST_MODULE = """import lemoncheesecake.api as lcc

@lcc.suite("My Suite")
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
from lemoncheesecake.matching import *

@lcc.suite("My Suite")
class mysuite:
    @lcc.test("My Test 1")
    def mytest1(self, fixt):
        check_that("val", fixt, equal_to(42))
"""


@pytest.fixture()
def project(tmp_cwd):
    generate_project(tmp_cwd, "mysuite", TEST_MODULE)


@pytest.fixture()
def failing_project(project):
    return project


@pytest.fixture()
def project_with_fixtures(tmp_cwd):
    generate_project(tmp_cwd, "mysuite", TEST_MODULE_USING_FIXTURES, FIXTURE_MODULE)


@pytest.fixture()
def successful_project(project_with_fixtures):
    return project_with_fixtures


@pytest.fixture()
def run_project_mock(mocker):
    return mocker.patch("lemoncheesecake.cli.commands.run.run_project")


def test_run_with_filter(project, cmdout):
    assert run_main(["run", "mysuite.mytest1"]) == 0
    assert_run_output(cmdout, "mysuite", failed_tests=["mytest1"])


def test_project_with_fixtures(project_with_fixtures, cmdout):
    assert run_main(["run", "mysuite.mytest1"]) == 0
    assert_run_output(cmdout, "mysuite", successful_tests=["mytest1"])


def test_stop_on_failure(project, cmdout):
    assert run_main(["run", "--stop-on-failure"]) == 0
    assert_run_output(cmdout, "mysuite", failed_tests=["mytest1"], skipped_tests=["mytest2"])


def test_cli_run(project, cmdout):
    assert run_main(["run"]) == 0
    assert_run_output(cmdout, "mysuite", successful_tests=["mytest2"], failed_tests=["mytest1"])


def test_project_path(tmpdir, cmdout):
    generate_project(tmpdir.strpath, "mysuite", TEST_MODULE)
    assert run_main(["run", "-p", tmpdir.strpath]) == 0
    assert_run_output(cmdout, "mysuite", successful_tests=["mytest2"], failed_tests=["mytest1"])


def test_cli_exit_error_on_failure_successful_suite(successful_project):
    assert run_main(["run", "--exit-error-on-failure"]) == 0


def test_cli_exit_error_on_failure_failing_suite(failing_project):
    assert run_main(["run", "--exit-error-on-failure"]) == 1


@lcc.suite("Sample Suite")
class SampleSuite:
    @lcc.test("test 1")
    def test_1(self):
        pass


class SampleProject(Project):
    def __init__(self, project_dir="."):
        Project.__init__(self, project_dir)

    def load_suites(self):
        return [load_suite_from_class(SampleSuite)]


def _test_run_suites_from_project(project, cli_args, expected_args):
    with patch("lemoncheesecake.cli.commands.run.PreparedProject") as mocked:
        run_suites_from_project(project, build_cli_args(["run"] + cli_args))
        mocked.create.assert_called_with(project, Any(), Any())
        mocked.create.return_value.run.assert_called_with(*expected_args)


class ReportingBackendMatcher(Matcher):
    def __init__(self, *expected):
        self.expected = expected

    def match(self, actual):
        return sorted([b.get_name() for b in actual]) == sorted(self.expected)


def test_run_suites_from_project_default():
    project = SampleProject(".")
    _test_run_suites_from_project(
        project, [],
        (ReportingBackendMatcher("json", "html", "console"),
         osp.join(os.getcwd(), "report"), savingstrategy.save_at_each_failed_test_strategy, False, False, 1)
    )


def test_run_suites_from_project_thread_cli_args():
    _test_run_suites_from_project(
        SampleProject(), ["--threads", "4"],
        (Any(), Any(), Any(), Any(), Any(), 4)
    )


def test_run_suites_from_project_thread_env():
    with env_vars(LCC_THREADS="4"):
        _test_run_suites_from_project(
            SampleProject(), [],
            (Any(), Any(), Any(), Any(), Any(), 4)
        )


def test_run_suites_from_project_thread_cli_args_while_threaded_is_disabled():
    project = SampleProject()
    project.threaded = False

    with pytest.raises(LemoncheesecakeException, match="does not support multi-threading"):
        _test_run_suites_from_project(project, ["--threads", "4"], None)


def test_run_suites_from_project_saving_strategy_cli_args():
    _test_run_suites_from_project(
        SampleProject(), ["--save-report", "at_each_failed_test"],
        (Any(), Any(), savingstrategy.save_at_each_failed_test_strategy, Any(), Any(), Any())
    )


def test_run_suites_from_project_saving_strategy_env():
    with env_vars(LCC_SAVE_REPORT="at_each_failed_test"):
        _test_run_suites_from_project(
            SampleProject(), [],
            (Any(), Any(), savingstrategy.save_at_each_failed_test_strategy, Any(), Any(), Any())
        )


def test_run_suites_from_project_reporting_backends_cli_args():
    _test_run_suites_from_project(
        SampleProject(), ["--reporting", "^console"],
        (ReportingBackendMatcher("json", "html"), Any(), Any(), Any(), Any(), Any())
    )


def test_run_suites_from_project_reporting_backends_env():
    with env_vars(LCC_REPORTING="^console"):
        _test_run_suites_from_project(
            SampleProject(), [],
            (ReportingBackendMatcher("json", "html"), Any(), Any(), Any(), Any(), Any())
        )


def test_run_suites_from_project_custom_attr_default_reporting_backend_names():
    project = SampleProject()
    project.default_reporting_backend_names = ["json", "html"]

    _test_run_suites_from_project(
        project, [],
        (ReportingBackendMatcher("json", "html"), Any(), Any(), Any(), Any(), Any())
    )


def test_run_suites_from_project_force_disabled_set():
    _test_run_suites_from_project(
        SampleProject(), ["--force-disabled"],
        (Any(), Any(), Any(), True, Any(), Any())
    )


def test_run_suites_from_project_stop_on_failure_set():
    _test_run_suites_from_project(
        SampleProject(), ["--stop-on-failure"],
        (Any(), Any(), Any(), Any(), True, Any())
    )


def test_run_suites_from_project_report_dir_through_project(tmpdir):
    report_dir = tmpdir.join("other_report_dir").strpath

    class MyProject(SampleProject):
        def create_report_dir(self):
            return report_dir

    _test_run_suites_from_project(
        MyProject(), [],
        (Any(), report_dir, Any(), Any(), Any(), Any())
    )


def test_run_suites_from_project_report_dir_cli_args(tmpdir):
    report_dir = tmpdir.join("other_report_dir").strpath

    _test_run_suites_from_project(
        SampleProject(), ["--report-dir", report_dir],
        (Any(), report_dir, Any(), Any(), Any(), Any())
    )


def test_run_suites_from_project_report_dir_env(tmpdir):
    report_dir = tmpdir.join("other_report_dir").strpath

    with env_vars(LCC_REPORT_DIR=report_dir):
        _test_run_suites_from_project(
            SampleProject(), [],
            (Any(), report_dir, Any(), Any(), Any(), Any())
        )
