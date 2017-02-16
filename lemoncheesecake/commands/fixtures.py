'''
Created on Feb 14, 2017

@author: nicolas
'''

import os

from termcolor import colored

from lemoncheesecake.cli import Command
from lemoncheesecake.testsuite.filter import add_filter_args_to_cli_parser, get_filter_from_cli_args
from lemoncheesecake.testsuite import walk_tests
from lemoncheesecake.project import find_project_file, Project
from lemoncheesecake.exceptions import ProjectError, ProgrammingError
from lemoncheesecake.fixtures import get_fixture_name, get_fixture_names, get_fixture_aliases, \
    get_fixture_scope, get_fixture_params, get_fixture_doc

def show_fixtures(scope, fixtures, used_by_tests, used_by_fixtures, verbose):
    B = lambda s: colored(s, attrs=["bold"])
    
    if fixtures:
        print "Fixtures for scope %s:" % B(scope)
        for fixt in fixtures:
            for fixt_name in get_fixture_names(fixt):
                test_usage = used_by_tests.get(fixt_name, 0)
                fixture_usage = used_by_fixtures.get(fixt_name, 0)
                if test_usage or fixture_usage:
                    usage = ""
                    if fixture_usage:
                        plural = "s" if fixture_usage > 1 else ""
                        usage = "used by %s fixture%s" % (B(fixture_usage), plural)
                    if test_usage:
                        plural = "s" if test_usage > 1 else ""
                        usage += " and %s test%s" % (B(test_usage), plural) if fixture_usage \
                            else "used by %s test%s" % (B(test_usage), plural)
                else:
                    usage = "unused"
                
                infos = [
                    ("doc", get_fixture_doc(fixt))
                ]
                
                print " * %s %s%s" % (
                    B(fixt_name), usage,
                    ", depends on %s" % "/".join(get_fixture_params(fixt)) if get_fixture_params(fixt) else ""
                )
                if verbose:
                    for info_name, info_value in infos:
                        if info_value:
                            print "   - %s: %s" % (info_name, info_value)
            
    else:
        print "Fixtures for scope %s: <none>" % colored(scope, attrs=["bold"])

class FixturesCommand(Command):
    def get_name(self):
        return "fixtures"
    
    def get_description(self):
        return "Show the fixtures available in the project"
    
    def add_cli_args(self, cli_parser):
        cli_parser.add_argument("--verbose", "-v", action="store_true", help="Show extra fixture information")

    def run_cmd(self, cli_args):
        project_file = find_project_file()
        if not project_file:
            return "Cannot find project file"
        try:
            project = Project(project_file)
            suites = project.load_testsuites()
            fixtures = project.get_fixtures()
        except (ProjectError, ProgrammingError) as e:
            return str(e)
        
        fixtures_by_scope = {}
        for fixt in fixtures:
            scope = get_fixture_scope(fixt)
            if scope in fixtures_by_scope:
                fixtures_by_scope[scope].append(fixt)
            else:
                fixtures_by_scope[scope] = [fixt]
        
        used_by_tests = {}
        def get_test_fixtures(test):
            for fixt_name in test.get_params():
                used_by_tests[fixt_name] = used_by_tests.get(fixt_name, 0) + 1
        walk_tests(suites, get_test_fixtures)
        
        used_by_fixtures = {}
        for fixt in fixtures:
            for param in get_fixture_params(fixt):
                used_by_fixtures[param] = used_by_fixtures.get(param, 0) + 1
        
        for scope in "session", "testsuite", "test":
            show_fixtures(scope, fixtures_by_scope.get(scope, []), used_by_tests, used_by_fixtures, cli_args.verbose)
            print
