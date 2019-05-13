import os
import pytest

from lemoncheesecake.cli import build_cli_args
from lemoncheesecake.cli.commands.run import run_project

from helpers.runner import generate_project, run_main
from helpers.cli import assert_run_output, cmdout
from helpers.project import DummyProject, DUMMY_SUITE


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

@lcc.suite("My Suite")
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
def failing_project(project):
    return project


@pytest.fixture()
def project_with_fixtures(tmpdir):
    generate_project(tmpdir.strpath, "mysuite", TEST_MODULE_USING_FIXTURES, FIXTURE_MODULE)
    old_cwd = os.getcwd()
    os.chdir(tmpdir.strpath)
    yield
    os.chdir(old_cwd)


@pytest.fixture()
def successful_project(project_with_fixtures):
    return project_with_fixtures


def test_run(project, cmdout):
    assert run_main(["run"]) == 0
    assert_run_output(cmdout, "mysuite", successful_tests=["mytest2"], failed_tests=["mytest1"])


def test_run_with_filter(project, cmdout):
    assert run_main(["run", "mysuite.mytest1"]) == 0
    assert_run_output(cmdout, "mysuite", failed_tests=["mytest1"])


def test_project_with_fixtures(project_with_fixtures, cmdout):
    assert run_main(["run", "mysuite.mytest1"]) == 0
    assert_run_output(cmdout, "mysuite", successful_tests=["mytest1"])


def test_stop_on_failure(project, cmdout):
    assert run_main(["run", "--stop-on-failure"]) == 0
    assert_run_output(cmdout, "mysuite", failed_tests=["mytest1"], skipped_tests=["mytest2"])


def test_exit_error_on_failure_successful_suite(successful_project):
    assert run_main(["run", "--exit-error-on-failure"]) == 0


def test_exit_error_on_failure_failing_suite(failing_project):
    assert run_main(["run", "--exit-error-on-failure"]) == 1


def test_pre_run(tmpdir):
    marker = []

    class MyProject(DummyProject):
        def pre_run(self, cli_args, report_dir):
            marker.append(cli_args.command)

    project = MyProject(tmpdir.strpath, [DUMMY_SUITE])

    # force the --reporting arguments to what the project really supports
    args = build_cli_args(["run"])
    args.reporting = project.reporting_backends

    run_project(project, args)

    assert marker == ["run"]


def test_post_run(tmpdir):
    marker = []

    class MyProject(DummyProject):
        def post_run(self, cli_args, report_dir):
            marker.append(cli_args.command)

    project = MyProject(tmpdir.strpath, [DUMMY_SUITE])

    # force the --reporting arguments to what the project really supports
    args = build_cli_args(["run"])
    args.reporting = project.reporting_backends

    run_project(project, args)

    assert marker == ["run"]
