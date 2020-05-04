import os
import os.path as osp
import re

import pytest

from lemoncheesecake.project import Project, create_project, find_project_file, load_project, run_project
from lemoncheesecake.suite import load_suite_from_class
from lemoncheesecake.fixture import load_fixtures_from_func
from lemoncheesecake.session import Session
from lemoncheesecake.reporting.savingstrategy import make_report_saving_strategy
from lemoncheesecake.reporting import JsonBackend
from lemoncheesecake.exceptions import LemoncheesecakeException, FixtureConstraintViolation, ProjectLoadingError
import lemoncheesecake.api as lcc

from helpers.utils import env_vars, tmp_cwd


def test_create_report_dir(tmpdir):
    project = Project(tmpdir.strpath)
    report_dir = project.create_report_dir()
    assert os.path.isdir(report_dir)


def test_reporting_backends(tmpdir):
    project = Project(tmpdir.strpath)

    expected_reporting_backends = ["console", "html", "json"]
    try:
        import lxml
        expected_reporting_backends.extend(["xml", "junit"])
    except ImportError:
        pass
    try:
        import reportportal_client
        expected_reporting_backends.append("reportportal")
    except ImportError:
        pass
    try:
        import slacker
        expected_reporting_backends.append("slack")
    except ImportError:
        pass

    assert sorted(project.reporting_backends.keys()) == sorted(expected_reporting_backends)


def test_default_reporting_backend_names(tmpdir):
    project = Project(tmpdir.strpath)
    assert project.default_reporting_backend_names == ["console", "json", "html"]


def test_project_creation(tmp_cwd):
    create_project(".")
    project = load_project()
    assert project.dir == tmp_cwd
    assert len(project.load_suites()) == 0
    assert len(project.load_fixtures()) == 0
    assert len(project.default_reporting_backend_names) > 0

    project.pre_run(object(), tmp_cwd)
    project.post_run(object(), tmp_cwd)


def test_load_project_while_no_project(tmp_cwd):
    with pytest.raises(ProjectLoadingError):
        load_project()


def test_load_project_while_project_file_in_current_dir(tmp_cwd):
    create_project(".")
    project = load_project()
    assert project


def test_load_project_while_suites_dir_in_current_dir(tmp_cwd):
    os.mkdir("suites")
    project = load_project()
    assert project.dir == tmp_cwd


def test_load_project_while_project_file_in_parent_dir(tmp_cwd):
    create_project(tmp_cwd)
    os.mkdir("subdir")
    os.chdir("subdir")
    project = load_project()
    assert project.dir == tmp_cwd


def test_load_project_while_project_file_env_var_not_found(tmpdir):
    with env_vars(LCC_PROJECT_FILE=tmpdir.join("project.py").strpath):
        with pytest.raises(ProjectLoadingError):
            load_project()


def test_load_project_while_project_file_env_var_found(tmpdir):
    create_project(tmpdir.strpath)

    with env_vars(LCC_PROJECT_FILE=tmpdir.join("project.py").strpath):
        project = load_project()
        assert project.dir == tmpdir.strpath


def test_run_project(tmpdir):
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.log_info("some log")

    class MyProject(Project):
        def load_suites(self):
            return [load_suite_from_class(suite)]

    project = MyProject(tmpdir.strpath)
    report = run_project(
        project, project.load_suites(), None, [], tmpdir.strpath, make_report_saving_strategy("at_end_of_tests")
    )

    assert report.is_successful()


def test_run_project_with_pre_run(tmpdir):
    pre_run_args = []

    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.log_info("some log")

    class MyProject(Project):
        def pre_run(self, cli_args, report_dir):
            pre_run_args.extend((cli_args, report_dir))

        def load_suites(self):
            return [load_suite_from_class(suite)]

    project = MyProject(tmpdir.strpath)
    report = run_project(
        project, project.load_suites(), NotImplemented, [], tmpdir.strpath, make_report_saving_strategy("at_end_of_tests")
    )

    assert report.is_successful()
    assert pre_run_args == [NotImplemented, tmpdir.strpath]


def test_run_project_with_pre_run_exception(tmpdir):
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.log_info("some log")

    class MyProject(Project):
        def pre_run(self, cli_args, report_dir):
            raise Exception("error from pre_run")

        def load_suites(self):
            return [load_suite_from_class(suite)]

    project = MyProject(tmpdir.strpath)

    with pytest.raises(LemoncheesecakeException, match=re.compile("error from pre_run")):
        run_project(
            project, project.load_suites(), NotImplemented, [], tmpdir.strpath, make_report_saving_strategy("at_end_of_tests")
        )


def test_run_project_with_post_run(tmpdir):
    post_run_args = []

    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.log_info("some log")

    class MyProject(Project):
        def post_run(self, cli_args, report_dir):
            post_run_args.extend((cli_args, report_dir))

        def load_suites(self):
            return [load_suite_from_class(suite)]

    project = MyProject(tmpdir.strpath)
    report = run_project(
        project, project.load_suites(), NotImplemented, [], tmpdir.strpath, make_report_saving_strategy("at_end_of_tests")
    )

    assert report.is_successful()
    assert post_run_args == [NotImplemented, tmpdir.strpath]


def test_run_project_with_post_run_exception(tmpdir):
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.log_info("some log")

    class MyProject(Project):
        def post_run(self, cli_args, report_dir):
            raise Exception("error from post_run")

        def load_suites(self):
            return [load_suite_from_class(suite)]

    project = MyProject(tmpdir.strpath)

    with pytest.raises(LemoncheesecakeException, match=re.compile("error from post_run")):
        run_project(
            project, project.load_suites(), NotImplemented, [], tmpdir.strpath, make_report_saving_strategy("at_end_of_tests")
        )

    session = Session.get()
    assert session.report.is_successful()


def test_run_project_with_build_report_title(tmpdir):
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.log_info("some log")

    class MyProject(Project):
        def build_report_title(self):
            return "Custom Report Title"

        def load_suites(self):
            return [load_suite_from_class(suite)]

    project = MyProject(tmpdir.strpath)
    report = run_project(
        project, project.load_suites(), NotImplemented, [], tmpdir.strpath, make_report_saving_strategy("at_end_of_tests")
    )

    assert report.is_successful()
    assert report.title == "Custom Report Title"


def test_run_project_with_build_report_info(tmpdir):
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.log_info("some log")

    class MyProject(Project):
        def build_report_info(self):
            return [("key", "value")]

        def load_suites(self):
            return [load_suite_from_class(suite)]

    project = MyProject(tmpdir.strpath)
    report = run_project(
        project, project.load_suites(), NotImplemented, [], tmpdir.strpath, make_report_saving_strategy("at_end_of_tests")
    )

    assert report.is_successful()
    assert report.info == [["key", "value"]]


def test_run_project_with_fixtures(tmpdir):
    test_args = []

    @lcc.fixture()
    def fixt():
        return 42

    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self, fixt):
            test_args.append(fixt)

    class MyProject(Project):
        def load_fixtures(self):
            return load_fixtures_from_func(fixt)

        def load_suites(self):
            return [load_suite_from_class(suite)]

    project = MyProject(tmpdir.strpath)
    report = run_project(
        project, project.load_suites(), NotImplemented, [], tmpdir.strpath,
        make_report_saving_strategy("at_end_of_tests")
    )

    assert report.is_successful()
    assert test_args == [42]


def test_run_project_with_fixture_error(tmpdir):
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self, missing_fixture):
            pass

    class MyProject(Project):
        def load_suites(self):
            return [load_suite_from_class(suite)]

    project = MyProject(tmpdir.strpath)
    with pytest.raises(FixtureConstraintViolation):
        run_project(
            project, project.load_suites(), NotImplemented, [], tmpdir.strpath,
            make_report_saving_strategy("at_end_of_tests")
        )


def test_run_project_with_fixture_cli_args(tmpdir):
    test_args = []

    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self, cli_args):
            test_args.append(cli_args)

    class MyProject(Project):
        def load_suites(self):
            return [load_suite_from_class(suite)]

    project = MyProject(tmpdir.strpath)
    report = run_project(
        project, project.load_suites(), NotImplemented, [], tmpdir.strpath,
        make_report_saving_strategy("at_end_of_tests")
    )

    assert report.is_successful()
    assert test_args == [NotImplemented]


def test_run_project_with_fixture_project_dir(tmpdir):
    test_args = []

    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self, project_dir):
            test_args.append(project_dir)

    class MyProject(Project):
        def load_suites(self):
            return [load_suite_from_class(suite)]

    project = MyProject(tmpdir.strpath)
    report = run_project(
        project, project.load_suites(), NotImplemented, [], tmpdir.strpath,
        make_report_saving_strategy("at_end_of_tests")
    )

    assert report.is_successful()
    assert test_args == [tmpdir.strpath]


def test_run_project_with_custom_nb_threads(tmpdir):
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.log_info("some log")

    class MyProject(Project):
        def load_suites(self):
            return [load_suite_from_class(suite)]

    project = MyProject(tmpdir.strpath)
    report = run_project(
        project, project.load_suites(), NotImplemented, [], tmpdir.strpath, make_report_saving_strategy("at_end_of_tests"),
        nb_threads=2
    )

    assert report.is_successful()
    assert report.nb_threads == 2


def test_run_project_with_force_disabled(tmpdir):
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        @lcc.disabled()
        def test(self):
            lcc.log_info("some log")

    class MyProject(Project):
        def load_suites(self):
            return [load_suite_from_class(suite)]

    project = MyProject(tmpdir.strpath)
    report = run_project(
        project, project.load_suites(), NotImplemented, [], tmpdir.strpath, make_report_saving_strategy("at_end_of_tests"),
        force_disabled=True
    )

    test, = list(report.all_tests())
    assert test.status == "passed"


def test_run_project_with_stop_on_failure(tmpdir):
    @lcc.suite("suite")
    class suite:
        @lcc.test("test_1")
        def test_1(self):
            lcc.log_error("something wrong happened")

        @lcc.test("test_2")
        def test_2(self):
            lcc.log_info("everything's fine")

    class MyProject(Project):
        def load_suites(self):
            return [load_suite_from_class(suite)]

    project = MyProject(tmpdir.strpath)
    report = run_project(
        project, project.load_suites(), NotImplemented, [], tmpdir.strpath, make_report_saving_strategy("at_end_of_tests"),
        stop_on_failure=True
    )

    test_1, test_2 = list(report.all_tests())
    assert test_1.status == "failed"
    assert test_2.status == "skipped"


def test_run_project_with_reporting_backends(tmpdir):
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.log_info("some log")

    class MyProject(Project):
        def load_suites(self):
            return [load_suite_from_class(suite)]

    project = MyProject(tmpdir.strpath)
    report = run_project(
        project, project.load_suites(), None, [JsonBackend()], tmpdir.strpath, make_report_saving_strategy("at_end_of_tests")
    )

    assert report.is_successful()
    assert tmpdir.join("report.js").exists()
