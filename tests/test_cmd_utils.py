from lemoncheesecake.cli.utils import auto_detect_reporting_backends
from lemoncheesecake.reporting.backend import get_reporting_backends

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
