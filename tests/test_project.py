import os
import argparse
import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.project import Project, SimpleProjectConfiguration, \
    HasCustomCliArgs, HasMetadataPolicy, HasPreRunHook, HasPostRunHook, create_project, load_project_from_dir, \
    find_project_file
from lemoncheesecake.suite import load_suite_from_class
from lemoncheesecake.validators import MetadataPolicy
from lemoncheesecake.exceptions import InvalidMetadataError

from helpers.runner import build_test_module, build_fixture_module


def make_test_project(project_dir):
    return Project(
        SimpleProjectConfiguration(project_dir.strpath),
        project_dir.strpath
    )


def test_get_project_dir(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(build_test_module())
    project = make_test_project(tmpdir)
    assert project.get_project_dir() == tmpdir


def test_get_suites(tmpdir):
    file = tmpdir.join("mysuite.py")
    file.write(build_test_module())
    project = make_test_project(tmpdir)
    suites = project.get_suites()
    assert len(suites) == 1 and suites[0].name == "mysuite"


def test_get_fixtures_without_fixtures(tmpdir):
    project = make_test_project(tmpdir)
    fixtures = project.get_fixtures()
    assert len(fixtures) == 0


def test_get_fixtures_with_fixtures(tmpdir):
    file = tmpdir.join("myfixtures.py")
    file.write(build_fixture_module("fixt"))
    project = Project(SimpleProjectConfiguration(tmpdir.strpath, tmpdir.strpath), tmpdir.strpath)
    fixtures = project.get_fixtures()
    assert len(fixtures) == 1 and fixtures[0].name == "fixt"


def test_create_report_dir(tmpdir):
    project = make_test_project(tmpdir)
    report_dir = project.create_report_dir()
    assert os.path.isdir(report_dir)


def test_get_all_reporting_backends(tmpdir):
    project = make_test_project(tmpdir)

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

    assert sorted([p.name for p in project.get_all_reporting_backends()]) == sorted(expected_reporting_backends)


def test_get_default_reporting_backends_for_test_run(tmpdir):
    project = make_test_project(tmpdir)
    assert [p.name for p in project.get_default_reporting_backends_for_test_run()] == ["console", "json", "html"]


def test_with_custom_cli_args(tmpdir):
    class MyProject(SimpleProjectConfiguration, HasCustomCliArgs):
        def add_custom_cli_args(self, cli_parser):
            cli_parser.add_argument("foobar")

    project = Project(MyProject(tmpdir.strpath), tmpdir.strpath)
    cli_parser = argparse.ArgumentParser()
    project.add_custom_args_to_run_cli(cli_parser)
    assert "foobar" in [a.dest for a in cli_parser._actions]


def test_without_custom_cli_args(tmpdir):
    project = make_test_project(tmpdir)
    cli_parser = argparse.ArgumentParser()
    project.add_custom_args_to_run_cli(cli_parser)


def test_with_pre_run_hook(tmpdir):
    marker = []

    class MyProject(SimpleProjectConfiguration, HasPreRunHook):
        def pre_run(self, report_dir):
            marker.append(1)

    project = Project(MyProject(tmpdir.strpath), tmpdir.strpath)
    project.run_pre_session_hook(tmpdir.strpath)
    assert len(marker) == 1


def test_without_pre_run_hook(tmpdir):
    project = make_test_project(tmpdir)
    project.run_pre_session_hook(tmpdir.strpath)


def test_with_post_run_hook(tmpdir):
    marker = []

    class MyProject(SimpleProjectConfiguration, HasPostRunHook):
        def post_run(self, report_dir):
            marker.append(1)

    project = Project(MyProject(tmpdir.strpath), tmpdir.strpath)
    project.run_post_session_hook(tmpdir.strpath)
    assert len(marker) == 1


def test_without_post_run_hook(tmpdir):
    project = make_test_project(tmpdir)
    project.run_post_session_hook(tmpdir.strpath)


def test_get_suites_with_metadatapolicy_check(tmpdir):
    @lcc.suite("My Suite")
    class mysuite:
        @lcc.test("My Test")
        @lcc.tags("mytag")
        def test(self):
            pass

    class MyProject(SimpleProjectConfiguration, HasMetadataPolicy):
        def get_metadata_policy(self):
            mp = MetadataPolicy()
            mp.disallow_unknown_tags()
            return mp

        def get_suites(self):
            return [load_suite_from_class(mysuite)]

    project = Project(MyProject(tmpdir.strpath), tmpdir.strpath)
    with pytest.raises(InvalidMetadataError):
        project.get_suites(check_metadata_policy=True)


def test_get_suites_without_metadatapolicy_check(tmpdir):
    @lcc.suite("My Suite")
    class mysuite:
        @lcc.test("My Test")
        @lcc.tags("mytag")
        def test(self):
            pass

    class MyProject(SimpleProjectConfiguration, HasMetadataPolicy):
        def get_metadata_policy(self):
            mp = MetadataPolicy()
            mp.disallow_unknown_tags()
            return mp

        def get_suites(self):
            return [load_suite_from_class(mysuite)]

    project = Project(MyProject(tmpdir.strpath), tmpdir.strpath)
    project.get_suites(check_metadata_policy=False)


def test_project_creation(tmpdir):
    create_project(tmpdir.strpath)
    project = load_project_from_dir(tmpdir.strpath)
    assert len(project.get_suites()) == 0
    assert len(project.get_fixtures()) == 0
    assert len(project.get_default_reporting_backends_for_test_run()) > 0

    project.run_pre_session_hook(tmpdir.strpath)
    project.run_post_session_hook(tmpdir.strpath)


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

# TODO: add tests on get_capabilities arguments
