import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.cli.utils import auto_detect_reporting_backends, load_suites_from_project
from lemoncheesecake.reporting.backend import get_reporting_backends
from lemoncheesecake.project import Project
from lemoncheesecake.suite import load_suite_from_class
from lemoncheesecake.exceptions import ValidationError, ProjectLoadingError

from helpers.runner import build_project_module
from helpers.utils import env_vars


def test_auto_detect_reporting_backends_no_project_found():
    backends = auto_detect_reporting_backends()
    assert sorted(b.get_name() for b in backends) == sorted(b.get_name() for b in get_reporting_backends())


def test_auto_detect_reporting_backends_invalid_project(tmpdir):
    tmpdir.join("project.py").write("THIS IS NOT A VALID PYTHON MODULE")

    with env_vars(LCC_PROJECT_FILE=tmpdir.join("project.py").strpath):
        with pytest.raises(ProjectLoadingError):
            auto_detect_reporting_backends()


def test_auto_detect_reporting_backends_custom_project(tmpdir):
    tmpdir.join("project.py").write(build_project_module("""
from lemoncheesecake.reporting.backends import ConsoleBackend

class MyProject(Project):
    def __init__(self, project_dir):
        Project.__init__(self, project_dir)
        self.reporting_backends = {"console": ConsoleBackend()}
"""))

    with env_vars(LCC_PROJECT_FILE=tmpdir.join("project.py").strpath):
        backends = auto_detect_reporting_backends()

    assert [b.get_name() for b in backends] == ["console"]


def test_load_suites_from_project(tmpdir):
    @lcc.suite()
    class mysuite:
        @lcc.test()
        def test(self):
            pass

    class MyProject(Project):
        def load_suites(self):
            return [load_suite_from_class(mysuite)]

    project = MyProject(tmpdir.strpath)
    assert len(load_suites_from_project(project)) == 1


def test_load_suites_from_project_with_filter(tmpdir):
    @lcc.suite()
    class mysuite:
        @lcc.test()
        def test_1(self):
            pass

        @lcc.test()
        def test_2(self):
            pass

    class MyProject(Project):
        def load_suites(self):
            return [load_suite_from_class(mysuite)]

    project = MyProject(tmpdir.strpath)
    suites = load_suites_from_project(project, lambda test: test.path == "mysuite.test_1")
    assert len(suites[0].get_tests()) == 1


def test_load_suites_from_project_with_filter_no_match(tmpdir):
    @lcc.suite()
    class mysuite:
        @lcc.test()
        def test_1(self):
            pass

        @lcc.test()
        def test_2(self):
            pass

    class MyProject(Project):
        def load_suites(self):
            return [load_suite_from_class(mysuite)]

    project = MyProject(tmpdir.strpath)
    with pytest.raises(lcc.UserError, match="does not match"):
        load_suites_from_project(project, lambda test: False)


def test_load_suites_from_empty(tmpdir):
    @lcc.suite()
    class mysuite:
        pass

    class MyProject(Project):
        def load_suites(self):
            return [load_suite_from_class(mysuite)]

    project = MyProject(tmpdir.strpath)
    with pytest.raises(lcc.UserError, match="No test is defined"):
        load_suites_from_project(project)
