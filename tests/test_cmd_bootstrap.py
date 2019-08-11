from helpers.runner import run_main

from lemoncheesecake.project import load_project_from_dir


def test_bootstrap(tmpdir):
    project_dir = tmpdir.join("myproj").strpath
    assert run_main(["bootstrap", project_dir]) == 0

    project = load_project_from_dir(project_dir)
    assert project.load_suites() == []


def test_bootstrap_existing_directory(tmpdir):
    out = run_main(["bootstrap", tmpdir.strpath])

    assert out.startswith("Cannot create project")
