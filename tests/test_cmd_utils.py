import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.cli.utils import auto_detect_reporting_backends, get_suites_from_project
from lemoncheesecake.reporting.backend import get_reporting_backends
from lemoncheesecake.project import Project
from lemoncheesecake.suite import load_suite_from_class
from lemoncheesecake.exceptions import InvalidMetadataError
from lemoncheesecake.cli.main import build_cli_args

from helpers.runner import build_project_module
from helpers.utils import env_var


def test_auto_detect_reporting_backends_no_project_found():
    backends = auto_detect_reporting_backends()
    assert sorted(b.get_name() for b in backends) == sorted(b.get_name() for b in get_reporting_backends())


def test_auto_detect_reporting_backends_invalid_project(tmpdir):
    tmpdir.join("project.py").write("THIS IS NOT A VALID PYTHON MODULE")

    with env_var("LCC_PROJECT_FILE", tmpdir.join("project.py").strpath):
        backends = auto_detect_reporting_backends()

    assert sorted(b.get_name() for b in backends) == sorted(b.get_name() for b in get_reporting_backends())


def test_auto_detect_reporting_backends_custom_project(tmpdir):
    tmpdir.join("project.py").write(build_project_module("""
from lemoncheesecake.reporting.backends import ConsoleBackend

class MyProject(Project):
    def __init__(self, project_dir):
        Project.__init__(self, project_dir)
        self.reporting_backends = {"console": ConsoleBackend()}
"""))

    with env_var("LCC_PROJECT_FILE", tmpdir.join("project.py").strpath):
        backends = auto_detect_reporting_backends()

    assert [b.get_name() for b in backends] == ["console"]


def test_get_suites_from_project_with_metadata_policy_ko(tmpdir):
    @lcc.suite("My Suite")
    class mysuite:
        @lcc.test("My Test")
        @lcc.tags("mytag")
        def test(self):
            pass

    class MyProject(Project):
        def __init__(self, project_dir):
            Project.__init__(self, project_dir)
            self.metadata_policy.disallow_unknown_tags()

        def get_suites(self):
            return [load_suite_from_class(mysuite)]

    project = MyProject(tmpdir.strpath)
    with pytest.raises(InvalidMetadataError):
        get_suites_from_project(project, build_cli_args(["show"]))


def test_get_suites_from_project_with_metadata_policy_ok(tmpdir):
    @lcc.suite("My Suite")
    class mysuite:
        @lcc.test("My Test")
        def test(self):
            pass

    class MyProject(Project):
        def __init__(self, project_dir):
            Project.__init__(self, project_dir)
            self.metadata_policy.disallow_unknown_tags()

        def get_suites(self):
            return [load_suite_from_class(mysuite)]

    project = MyProject(tmpdir.strpath)
    get_suites_from_project(project, build_cli_args(["show"]))
