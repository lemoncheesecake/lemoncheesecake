import os

from helpers.runner import run_main
from helpers.utils import tmp_cwd

from lemoncheesecake.project import load_project


def test_bootstrap(tmp_cwd):
    assert run_main(["bootstrap", "myproject"]) == 0

    os.chdir("myproject")
    project = load_project()
    assert project.load_suites() == []


def test_bootstrap_existing_directory(tmpdir):
    out = run_main(["bootstrap", tmpdir.strpath])

    assert out.startswith("Cannot create project")
