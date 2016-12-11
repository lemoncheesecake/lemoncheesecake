import sys
import argparse

from lemoncheesecake.project import Project
from lemoncheesecake.reporting import backends

from helpers import build_test_project, build_test_module

def set_project_testsuites_param(params, testsuite_name, project_dir):
    testsuite_file = project_dir.join("%s.py" % testsuite_name)
    testsuite_file.write(build_test_module(testsuite_name))
    params["TESTSUITES"] = "[ loader.import_testsuite_from_file('%s.py') ]" % (testsuite_name)    

def test_project_minimal_parameters(tmpdir):
    params = {}
    set_project_testsuites_param(params, "mysuite", tmpdir)
    project_file = tmpdir.join("project.py")
    project_file.write(build_test_project(params))
    project = Project(project_file.strpath)

    assert project.get_project_dir() == tmpdir.strpath

    classes = project.get_testsuites_classes()
    assert classes[0].__name__ == "mysuite"
    
    assert project.get_report_dir_creation_cb() != None
    
    assert [p.name for p in project.get_available_reporting_backends()] == ["console", "json", "html"]
    
    assert len(project.get_workers()) == 0
    
    assert project.get_metadata_policy().has_constraints() == False

def test_project_with_available_reporting_backends(tmpdir):
    params = {}
    set_project_testsuites_param(params, "mysuite", tmpdir)
    params["REPORTING_BACKENDS_AVAILABLE"] = "[ backends.ConsoleBackend() ]"
    project_file = tmpdir.join("project.py")
    project_file.write(build_test_project(params))
    
    project = Project(project_file.strpath)
    
    assert [p.name for p in project.get_available_reporting_backends()] == ["console"]

def test_project_with_enabled_reporting_backends(tmpdir):
    params = {}
    set_project_testsuites_param(params, "mysuite", tmpdir)
    params["REPORTING_BACKENDS_ENABLED"] = "[ 'console', 'json' ]"
    project_file = tmpdir.join("project.py")
    project_file.write(build_test_project(params))
        
    project = Project(project_file.strpath)
    
    assert project.get_enabled_reporting_backends() == ["console", "json"]

def test_project_with_workers(tmpdir):
    params = {}
    set_project_testsuites_param(params, "mysuite", tmpdir)
    worker_code = """
class MyWorker(workers.Worker):
    pass
"""
    params["WORKERS"] = "{'myworker': MyWorker()}"
    project_file = tmpdir.join("project.py")
    project_file.write(build_test_project(params, static_content=worker_code))
    
    project = Project(project_file.strpath)
    
    workers = project.get_workers()
    assert len(workers) == 1
    assert list(workers.keys()) == ["myworker"]
    assert workers["myworker"].__class__.__name__ == "MyWorker"

def test_project_with_metadata_policy(tmpdir):
    params = {}
    set_project_testsuites_param(params, "mysuite", tmpdir)
    policy_code = """
metadata_policy = validators.MetadataPolicy()
metadata_policy.disallow_unknown_tags()
"""
    params["METADATA_POLICY"] = "metadata_policy"
    project_file = tmpdir.join("project.py")
    project_file.write(build_test_project(params, static_content=policy_code))
    
    project = Project(project_file.strpath)
    
    assert project.get_metadata_policy().has_constraints() == True

def test_project_with_report_dir_creation(tmpdir):
    params = {}
    set_project_testsuites_param(params, "mysuite", tmpdir)
    cli_args_code = """
def custom_report_dir(top_dir):
    pass
"""
    params["REPORT_DIR_CREATION"] = "custom_report_dir"
    project_file = tmpdir.join("project.py")
    project_file.write(build_test_project(params, static_content=cli_args_code))
    
    project = Project(project_file.strpath)

    assert project.get_report_dir_creation_cb().__name__ == "custom_report_dir"

def test_project_with_cli_extra_args(tmpdir):
    params = {}
    set_project_testsuites_param(params, "mysuite", tmpdir)
    cli_args_code = """
def add_cli_args(cli_parser):
    cli_parser.add_argument("foobar")
"""
    params["CLI_EXTRA_ARGS"] = "add_cli_args"
    project_file = tmpdir.join("project.py")
    project_file.write(build_test_project(params, static_content=cli_args_code))
    
    project = Project(project_file.strpath)

    cli_parser = argparse.ArgumentParser()
    project.add_cli_extra_args(cli_parser)
    
    assert "foobar" in [a.dest for a in cli_parser._actions]