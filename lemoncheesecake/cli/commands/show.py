'''
Created on Feb 14, 2017

@author: nicolas
'''

from __future__ import print_function

from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import get_suites_from_project
from lemoncheesecake.filter import add_filter_args_to_cli_parser
from lemoncheesecake.project import load_project


class ShowCommand(Command):
    def get_name(self):
        return "show"
    
    def get_description(self):
        return "Show the test tree"
    
    def add_cli_args(self, cli_parser):
        add_filter_args_to_cli_parser(cli_parser)

        group = cli_parser.add_argument_group("Display")
        group.add_argument("--no-metadata", "-i", action="store_true", help="Hide suite and test metadata")
        group.add_argument("--short", "-s", action="store_true", help="Display suite and test names instead of path")
        group.add_argument("--desc-mode", "-d", action="store_true", help="Display suite and test descriptions instead of path")
        group.add_argument("--flat-mode", "-f", action="store_true", help="Enable flat mode: display all test and suite as path without indentation nor prefix")
        self.add_color_cli_args(group)

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
        return test.get_path_as_str()

    def get_suite_label(self, suite):
        if self.show_description:
            return suite.description
        if self.short:
            return suite.name
        return suite.get_path_as_str()

    def show_test(self, test, suite):
        md = self.serialize_metadata(test) if self.show_metadata else ""
        if self.flat_mode:
            print("%s%s" % (self.get_test_label(test, suite), " (%s)" % md if md else ""))
        else:
            padding = self.get_padding(suite.get_depth() + 1)
            test_label = self.get_test_label(test, suite)
            print("%s- %s%s" % (padding, test_label, " (%s)" % md if md else ""))
        
    def show_suite(self, suite):
        md = self.serialize_metadata(suite) if self.show_metadata else ""
        if self.flat_mode:
            print("%s%s" % (self.bold(self.get_suite_label(suite)), " (%s)" % md if md else ""))
        else:
            padding = self.get_padding(suite.get_depth())
            suite_label = self.get_suite_label(suite)
            print("%s* %s%s:" % (padding, self.bold(suite_label), " (%s)" % md if md else ""))

        for test in suite.get_tests():
            self.show_test(test, suite)

        for sub_suite in suite.get_suites():
            self.show_suite(sub_suite)
    
    def show_suites(self, suites):
        for suite in suites:
            self.show_suite(suite)

    def run_cmd(self, cli_args):
        self.process_color_cli_args(cli_args)

        self.short = cli_args.short
        self.show_description = cli_args.desc_mode
        self.show_metadata = not cli_args.no_metadata
        self.flat_mode = cli_args.flat_mode
        self.indent = 4

        project = load_project()
        suites = get_suites_from_project(project, cli_args)
        
        self.show_suites(suites)
        
        return 0