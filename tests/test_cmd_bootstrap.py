import os.path as osp

from helpers import cmdout

from lemoncheesecake.cli import main
from lemoncheesecake.project import Project

def test_bootstrap(tmpdir):
    project_dir = tmpdir.join("myproj").strpath
    assert main(["bootstrap", project_dir]) == 0
    
    project = Project(osp.join(project_dir, "project.py"))
    assert project.get_testsuites() == []

def test_bootstrap_existing_directory(tmpdir):
    out = main(["bootstrap", tmpdir.strpath])
    
    assert out.startswith("Cannot create project")
