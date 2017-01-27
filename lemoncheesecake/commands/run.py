'''
Created on Dec 31, 2016

@author: nicolas
'''

import os

from lemoncheesecake.cli import Command
from lemoncheesecake.project import find_project_file, Project
from lemoncheesecake.fixtures import FixtureRegistry, BuiltinFixture, load_fixtures_from_func
from lemoncheesecake.runner import run_testsuites
from lemoncheesecake.testsuite.filter import add_filter_args_to_cli_parser, get_filter_from_cli_args
from lemoncheesecake import reporting
from lemoncheesecake.exceptions import ProjectError, FixtureError

class RunCommand(Command):
    def get_name(self):
        return "run"
    
    def get_description(self):
        return "Run tests"
    
    def add_cli_args(self, cli_parser):
        project_file = find_project_file()
        default_reporting_backend_names = []
        if project_file:
            try:
                project = Project(project_file)
                default_reporting_backend_names = project.get_active_reporting_backend_names()
            except:
                # do nothing if it fails here, otherwise
                # the user won't even be able to get the command usage
                pass
            else:
                project.add_cli_extra_args(cli_parser)
            
        add_filter_args_to_cli_parser(cli_parser)
        cli_parser.add_argument("--report-dir", "-r", required=False, help="Directory where report data will be stored")
        cli_parser.add_argument("--reporting", nargs="+", required=False,
            help="The list of reporting backends to use", default=default_reporting_backend_names
        )
        cli_parser.add_argument("--enable-reporting", nargs="+", required=False,
            help="The list of reporting backends to add (to base backends)"
        )
        cli_parser.add_argument("--disable-reporting", nargs="+", required=False,
            help="The list of reporting backends to remove (from base backends)"
        )
    
    def run_cmd(self, cli_args):
        ###
        # Project initialization
        ###
        project_file = find_project_file()
        if not project_file:
            return "Cannot find project file"
        try:
            project = Project(project_file)
        except ProjectError as e:
            return str(e)
        testsuites = project.load_testsuites()
        if len(testsuites) == 0:
            return "No testsuites are defined in your lemoncheesecake project."
    
        fixture_registry = FixtureRegistry()
        fixture_registry.add_fixture(BuiltinFixture("cli_args", lambda: cli_args))
        fixture_registry.add_fixture(BuiltinFixture("project_dir", lambda: project.get_project_dir()))
        for fixture_func in project.get_fixtures():
            fixture_registry.add_fixtures(load_fixtures_from_func(fixture_func))
        try:
            fixture_registry.check_dependencies()
        except FixtureError as e:
            return str(e)
        workers = project.get_workers()
        reporting_backends = { 
            backend.name: backend for backend in
                project.get_reporting_backends(capabilities=reporting.CAPABILITY_REPORTING_SESSION, active_only=False)
        }
        default_report_dir_creation_callback = project.get_report_dir_creation_callback()
        before_run_hook = project.get_before_test_run_hook()
        after_run_hook = project.get_after_test_run_hook()
        
        ###
        # Process CLI arguments
        ###
        # apply filter
        filter = get_filter_from_cli_args(cli_args)
        if not filter.is_empty():
            tmp = []
            for suite in testsuites:
                suite.apply_filter(filter)
                if suite.has_selected_tests():
                    tmp.append(suite)
            if not tmp:
                return "The test filter does not match any test."
            testsuites = tmp
    
        # set reporting backends
        reporting_backend_names = set(cli_args.reporting)
        if cli_args.enable_reporting:
            for backend in cli_args.enable_reporting:
                reporting_backend_names.add(backend)
        if cli_args.disable_reporting:
            for backend in cli_args.disable_reporting:
                reporting_backend_names.remove(backend)
        
        # initialize workers using CLI
        for worker in workers.values():
            worker.cli_initialize(cli_args)
        
        # create report dir
        if cli_args.report_dir:
            report_dir = cli_args.report_dir
            os.mkdir(report_dir)
        else:
            report_dir = default_report_dir_creation_callback(project.get_project_dir())
    
        ###
        # Run tests
        ###
        if before_run_hook:
            before_run_hook(report_dir)
        
        run_testsuites(
            testsuites, fixture_registry, workers, [reporting_backends[backend_name] for backend_name in reporting_backend_names], report_dir
        )
        
        if after_run_hook:
            after_run_hook(report_dir)
        
        return 0
