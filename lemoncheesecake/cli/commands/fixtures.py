'''
Created on Feb 14, 2017

@author: nicolas
'''

from __future__ import print_function

from lemoncheesecake.cli.display import print_table
from lemoncheesecake.cli.command import Command
from lemoncheesecake.testsuite import walk_tests
from lemoncheesecake.project import find_project_file, Project
from lemoncheesecake.exceptions import ProjectError, ProgrammingError
from lemoncheesecake.fixtures import get_fixture_name, get_fixture_names, get_fixture_scope, get_fixture_params

class FixturesCommand(Command):
    def get_name(self):
        return "fixtures"
    
    def get_description(self):
        return "Show the fixtures available in the project"
    
    def add_cli_args(self, cli_parser):
        self.add_color_cli_args(cli_parser)
        cli_parser.add_argument("--verbose", "-v", action="store_true", help="Show extra fixture information")

    def show_fixtures(self, scope, fixtures, used_by_tests, used_by_fixtures, verbose):
        lines = []
        ordered_fixtures = sorted(
            fixtures,
            key=lambda f: used_by_fixtures.get(get_fixture_name(f), 0) + used_by_tests.get(get_fixture_name(f), 0),
            reverse=True
        )
        for fixt in ordered_fixtures:
            for fixt_name in get_fixture_names(fixt):
                lines.append([
                    self.bold(fixt_name), ", ".join(get_fixture_params(fixt) or "-"),
                    used_by_fixtures.get(fixt_name, 0), used_by_tests.get(fixt_name, 0)
                ])
        print_table("Fixture with scope %s" % self.bold(scope), ["Fixture", "Dependencies", "Used by fixtures", "Used by tests"], lines)
    
    def run_cmd(self, cli_args):
        self.process_color_cli_args(cli_args)
        
        project_file = find_project_file()
        if not project_file:
            return "Cannot find project file"
        try:
            project = Project(project_file)
            suites = project.get_testsuites()
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
        def get_test_fixtures(test, suite):
            for fixt_name in test.get_params():
                used_by_tests[fixt_name] = used_by_tests.get(fixt_name, 0) + 1
        walk_tests(suites, get_test_fixtures)
        
        used_by_fixtures = {}
        for fixt in fixtures:
            for param in get_fixture_params(fixt):
                used_by_fixtures[param] = used_by_fixtures.get(param, 0) + 1
        
        for scope in "session_prerun", "session", "testsuite", "test":
            self.show_fixtures(scope, fixtures_by_scope.get(scope, []), used_by_tests, used_by_fixtures, cli_args.verbose)
            print()

        return 0