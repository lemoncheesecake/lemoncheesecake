'''
Created on Feb 14, 2017

@author: nicolas
'''

from __future__ import print_function

from lemoncheesecake.cli import Command
from lemoncheesecake.testsuite.filter import add_filter_args_to_cli_parser, get_filter_from_cli_args
from lemoncheesecake.project import find_project_file, Project
from lemoncheesecake.exceptions import ProjectError, ProgrammingError
from lemoncheesecake.testsuite import filter_testsuites

class ShowCommand(Command):
    def get_name(self):
        return "show"
    
    def get_description(self):
        return "Show the test tree"
    
    def add_cli_args(self, cli_parser):
        cli_parser.add_argument("--no-metadata", "-i", action="store_true", help="Hide testsuite and test metadata")
        cli_parser.add_argument("--short", "-s", action="store_true", help="Display testsuite and test names instead of path")
        cli_parser.add_argument("--desc-mode", "-d", action="store_true", help="Display testsuite and test descriptions instead of path")
        cli_parser.add_argument("--flat-mode", "-f", action="store_true", help="Enable flat mode: display all test and testsuite as path without indentation nor prefix")
        self.add_color_cli_args(cli_parser)
        add_filter_args_to_cli_parser(cli_parser)

    def get_padding(self, depth):
        return " " * (depth * self.indent)
    
    def serialize_metadata(self, obj):
        return ", ".join(
            obj.tags +
            ["%s:%s" % (k, v) for k, v in obj.properties.items()] +
            [link_name or link_url for link_url, link_name in obj.links]
        )
    
    def get_test_label(self, test, suite):
        if self.show_description:
            return test.description
        if self.short:
            return test.name
        return suite.get_test_path_str(test)
    
    def get_suite_label(self, suite):
        if self.show_description:
            return suite.description
        if self.short:
            return suite.name
        return suite.get_path_str()
    
    def show_test(self, test, suite):
        md = self.serialize_metadata(test) if self.show_metadata else ""
        if self.flat_mode:
            print("%s%s" % (self.get_test_label(test, suite), " (%s)" % md if md else ""))
        else:
            padding = self.get_padding(suite.get_depth() + 1)
            test_label = self.get_test_label(test, suite)
            print("%s- %s%s" % (padding, test_label, " (%s)" % md if md else ""))
        
    def show_testsuite(self, suite):
        md = self.serialize_metadata(suite) if self.show_metadata else ""
        if self.flat_mode:
            print("%s%s" % (self.bold(self.get_suite_label(suite)), " (%s)" % md if md else ""))
        else:
            padding = self.get_padding(suite.get_depth())
            suite_label = self.get_suite_label(suite)
            print("%s* %s%s:" % (padding, self.bold(suite_label), " (%s)" % md if md else ""))

        for test in suite.get_tests():
            self.show_test(test, suite)
        
        for sub_suite in suite.get_sub_testsuites():
            self.show_testsuite(sub_suite)
    
    def show_testsuites(self, suites):
        for suite in suites:
            self.show_testsuite(suite)

    def run_cmd(self, cli_args):
        self.process_color_cli_args(cli_args)

        self.short = cli_args.short
        self.show_description = cli_args.desc_mode
        self.show_metadata = not cli_args.no_metadata
        self.flat_mode = cli_args.flat_mode
        self.indent = 4

        project_file = find_project_file()
        if not project_file:
            return "Cannot find project file"
        try:
            project = Project(project_file)
            suites = project.load_testsuites()
        except (ProjectError, ProgrammingError) as e:
            return str(e)
        
        filt = get_filter_from_cli_args(cli_args)
        suites = filter_testsuites(suites, filt)
        
        self.show_testsuites(suites)
        
        return 0