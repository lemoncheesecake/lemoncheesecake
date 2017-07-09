import os.path as osp

from helpers import cmdout

from lemoncheesecake.cli import main
from lemoncheesecake.project import load_project

def test_bootstrap(tmpdir):
    project_dir = tmpdir.join("myproj").strpath
    assert main(["bootstrap", project_dir]) == 0

    project = load_project(project_dir)
    assert project.get_suites() == []

def test_bootstrap_existing_directory(tmpdir):
    out = main(["bootstrap", tmpdir.strpath])

    assert out.startswith("Cannot create project")
