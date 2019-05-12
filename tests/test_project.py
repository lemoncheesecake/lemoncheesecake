import os
import argparse
import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.project import Project, create_project, load_project_from_dir, find_project_file
from lemoncheesecake.suite import load_suite_from_class
from lemoncheesecake.validators import MetadataPolicy
from lemoncheesecake.exceptions import InvalidMetadataError

from helpers.runner import build_test_module, build_fixture_module


def test_project_dir(tmpdir):
    file = tmpdir.mkdir("suites").join("mysuite.py")
    file.write(build_test_module())
    project = Project(tmpdir.strpath)
    assert project.dir == tmpdir


def test_get_suites(tmpdir):
    file = tmpdir.mkdir("suites").join("mysuite.py")
    file.write(build_test_module())
    project = Project(tmpdir.strpath)
    suites = project.get_suites()
    assert len(suites) == 1 and suites[0].name == "mysuite"


def test_get_fixtures_without_fixtures(tmpdir):
    project = Project(tmpdir.strpath)
    fixtures = project.get_fixtures()
    assert len(fixtures) == 0


def test_get_fixtures_with_fixtures(tmpdir):
    file = tmpdir.mkdir("fixtures").join("myfixtures.py")
    file.write(build_fixture_module("fixt"))
    project = Project(tmpdir.strpath)
    fixtures = project.get_fixtures()
    assert len(fixtures) == 1 and fixtures[0].name == "fixt"


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


def test_with_custom_cli_args(tmpdir):
    class MyProject(Project):
        def add_custom_cli_args(self, cli_parser):
            cli_parser.add_argument("foobar")

    project = MyProject(tmpdir.strpath)
    cli_parser = argparse.ArgumentParser()
    project.add_custom_cli_args(cli_parser)
    assert "foobar" in [a.dest for a in cli_parser._actions]


def test_without_custom_cli_args(tmpdir):
    project = Project(tmpdir.strpath)
    cli_parser = argparse.ArgumentParser()
    project.add_custom_cli_args(cli_parser)


def test_with_pre_run_hook(tmpdir):
    marker = []

    class MyProject(Project):
        def pre_run(self, cli_args, report_dir):
            marker.append(1)

    project = MyProject(tmpdir.strpath)
    project.pre_run(object(), tmpdir.strpath)
    assert len(marker) == 1


def test_without_pre_run_hook(tmpdir):
    project = Project(tmpdir.strpath)
    project.pre_run(object(), tmpdir.strpath)


def test_with_post_run_hook(tmpdir):
    marker = []

    class MyProject(Project):
        def post_run(self, cli_args, report_dir):
            marker.append(1)

    project = MyProject(tmpdir.strpath)
    project.post_run(object(), tmpdir.strpath)
    assert len(marker) == 1


def test_without_post_run_hook(tmpdir):
    project = Project(tmpdir.strpath)
    project.post_run(object(), tmpdir.strpath)


def test_get_suites_with_metadatapolicy_check(tmpdir):
    @lcc.suite("My Suite")
    class mysuite:
        @lcc.test("My Test")
        @lcc.tags("mytag")
        def test(self):
            pass

    class MyProject(Project):
        def get_metadata_policy(self):
            mp = MetadataPolicy()
            mp.disallow_unknown_tags()
            return mp

        def get_suites(self):
            return [load_suite_from_class(mysuite)]

    project = MyProject(tmpdir.strpath)
    with pytest.raises(InvalidMetadataError):
        project.get_suites_strict()


def test_get_suites_without_metadatapolicy_check(tmpdir):
    @lcc.suite("My Suite")
    class mysuite:
        @lcc.test("My Test")
        @lcc.tags("mytag")
        def test(self):
            pass

    class MyProject(Project):
        def get_metadata_policy(self):
            mp = MetadataPolicy()
            mp.disallow_unknown_tags()
            return mp

        def get_suites(self):
            return [load_suite_from_class(mysuite)]

    project = MyProject(tmpdir.strpath)
    project.get_suites()


def test_project_creation(tmpdir):
    create_project(tmpdir.strpath)
    project = load_project_from_dir(tmpdir.strpath)
    assert len(project.get_suites()) == 0
    assert len(project.get_fixtures()) == 0
    assert len(project.default_reporting_backend_names) > 0

    project.pre_run(object(), tmpdir.strpath)
    project.post_run(object(), tmpdir.strpath)


def test_find_project_file_not_found(tmpdir):
    old_cwd = os.getcwd()
    os.chdir(tmpdir.strpath)
    try:
        actual = find_project_file()
        assert actual is None
    finally:
        os.chdir(old_cwd)


def test_find_project_file_in_current_dir(tmpdir):
    old_cwd = os.getcwd()
    os.chdir(tmpdir.strpath)
    try:
        tmpdir.join("project.py").write("")
        actual = find_project_file()
        assert actual == tmpdir.join("project.py").strpath
    finally:
        os.chdir(old_cwd)


def test_find_project_file_in_parent_dir(tmpdir):
    old_cwd = os.getcwd()
    tmpdir.join("project.py").write("")
    tmpdir.join("subdir").mkdir()
    os.chdir(tmpdir.join("subdir").strpath)
    try:
        actual = find_project_file()
        assert actual == tmpdir.join("project.py").strpath
    finally:
        os.chdir(old_cwd)


def test_find_project_file_env_var_not_found(tmpdir):
    os.environ["LCC_PROJECT_FILE"] = tmpdir.join("project.py").strpath
    try:
        actual = find_project_file()
        assert actual is None
    finally:
        del os.environ["LCC_PROJECT_FILE"]


def test_find_project_file_env_var_found(tmpdir):
    tmpdir.join("project.py").write("")
    os.environ["LCC_PROJECT_FILE"] = tmpdir.join("project.py").strpath

    try:
        actual = find_project_file()
        assert actual == tmpdir.join("project.py").strpath
    finally:
        del os.environ["LCC_PROJECT_FILE"]
