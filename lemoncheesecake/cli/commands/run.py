'''
Created on Dec 31, 2016

@author: nicolas
'''

import os

from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import filter_testsuites_from_cli_args
from lemoncheesecake.project import find_project_file, Project
from lemoncheesecake.fixtures import FixtureRegistry, BuiltinFixture, load_fixtures_from_func
from lemoncheesecake.runner import run_testsuites
from lemoncheesecake.testsuite.filter import add_filter_args_to_cli_parser
from lemoncheesecake import reporting
from lemoncheesecake.exceptions import ProjectError, FixtureError, InvalidMetadataError,\
    ProgrammingError, LemonCheesecakeException, UserError, serialize_current_exception

def build_fixture_registry(project, cli_args):
    registry = FixtureRegistry()
    registry.add_fixture(BuiltinFixture("cli_args", lambda: cli_args))
    registry.add_fixture(BuiltinFixture("project_dir", lambda: project.get_project_dir()))
    for fixture in project.get_fixtures():
        registry.add_fixture(fixture)
    registry.check_dependencies()
    return registry

class RunCommand(Command):
    def get_name(self):
        return "run"
    
    def get_description(self):
        return "Run the tests"
    
    def add_cli_args(self, cli_parser):
        project_file = find_project_file()
        project = None
        default_reporting_backend_names = []
        if project_file:
            project = Project(project_file)
            default_reporting_backend_names = project.get_active_reporting_backend_names()
            
        add_filter_args_to_cli_parser(cli_parser)
        
        group = cli_parser.add_argument_group("Reporting")
        group.add_argument("--report-dir", "-r", required=False, help="Directory where report data will be stored")
        group.add_argument("--reporting", nargs="+", default=default_reporting_backend_names,
            help="The list of reporting backends to use"
        )
        group.add_argument("--enable-reporting", nargs="+", default=[],
            help="The list of reporting backends to add (to base backends)"
        )
        group.add_argument("--disable-reporting", nargs="+", default=[],
            help="The list of reporting backends to remove (from base backends)"
        )

        if project:
            project.add_cli_extra_args(cli_parser)

    def run_cmd(self, cli_args):
        # Project initialization
        project_file = find_project_file()
        if not project_file:
            return "Cannot find project file"
        try:
            project = Project(project_file)
            testsuites = project.get_testsuites()
        except (ProjectError, ProgrammingError) as e:
            return str(e)
        except InvalidMetadataError as e:
            return "Invalid test/testsuite metadata has been found: %s" % e

        # Build fixture registry
        try:
            fixture_registry = build_fixture_registry(project, cli_args)
            fixture_registry.check_fixtures_in_testsuites(testsuites)
        except FixtureError as e:
            return "Cannot run tests: %s" % e
        
        reporting_backends = { 
            backend.name: backend for backend in
                project.get_reporting_backends(capabilities=reporting.CAPABILITY_REPORTING_SESSION, active_only=False)
        }
        default_report_dir_creation_callback = project.get_report_dir_creation_callback()
        before_run_hook = project.get_before_test_run_hook()
        after_run_hook = project.get_after_test_run_hook()
        
        testsuites = filter_testsuites_from_cli_args(testsuites, cli_args)
        
        # Set reporting backends
        selected_reporting_backends = set()
        for backend_name in cli_args.reporting + cli_args.enable_reporting:
            try:
                selected_reporting_backends.add(reporting_backends[backend_name])
            except KeyError:
                return "Unknown reporting backend '%s'" % backend_name
        for backend_name in cli_args.disable_reporting:
            try:
                selected_reporting_backends.discard(reporting_backends[backend_name])
            except KeyError:
                return "Unknown reporting backend '%s'" % backend_name
        
        # Create report dir
        if cli_args.report_dir:
            report_dir = cli_args.report_dir
            try:
                os.mkdir(report_dir)
            except Exception as e:
                return "Cannot create report directory: %s" % e
        else:
            project_dir = project.get_project_dir()
            try:
                report_dir = default_report_dir_creation_callback(project_dir)
            except UserError as e:
                return str(e)
            except Exception:
                return "Got an unexpected exception while creating report directory:%s" % \
                    serialize_current_exception(show_stacktrace=True)
    
        # Handle before run hook 
        if before_run_hook:
            try:
                before_run_hook(report_dir)
            except UserError as e:
                return str(e)
            except Exception:
                return "Got an unexpected exception while running the before-run hook:%s" % \
                    serialize_current_exception(show_stacktrace=True)
        
        # Run tests 
        try:
            run_testsuites(
                testsuites, fixture_registry, selected_reporting_backends, report_dir
            )
        except LemonCheesecakeException as e:
            return str(e)
        
        # Handle after run hook 
        if after_run_hook:
            try:
                after_run_hook(report_dir)
            except UserError as e:
                return str(e)
            except Exception:
                return "Got an unexpected exception while running the after-run hook:%s" % (
                    serialize_current_exception(show_stacktrace=True)
                )
        
        return 0
