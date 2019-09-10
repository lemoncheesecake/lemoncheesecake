'''
Created on Feb 14, 2017

@author: nicolas
'''

from __future__ import print_function

from lemoncheesecake.helpers.console import bold
from lemoncheesecake.helpers.text import ensure_single_line_text
from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import load_suites_from_project
from lemoncheesecake.filter import add_test_filter_cli_args, make_test_filter
from lemoncheesecake.project import load_project
from lemoncheesecake.reporting.console import serialize_metadata


class TestTreeRenderer(object):
    def __init__(self, show_description=False, indent=4):
        self.show_description = show_description
        self.indent = indent

    def get_padding(self, depth):
        return " " * (depth * self.indent)

    def get_test_label(self, test):
        if self.show_description:
            return ensure_single_line_text(test.description)
        else:
            return test.path

    def get_suite_label(self, suite):
        if self.show_description:
            return ensure_single_line_text(suite.description)
        else:
            return suite.path

    def show_test(self, test, suite):
        md = serialize_metadata(test)
        padding = self.get_padding(suite.hierarchy_depth + 1)
        test_label = self.get_test_label(test)
        print("%s- %s%s" % (padding, test_label, " (%s)" % md if md else ""))

    def show_suite(self, suite):
        md = serialize_metadata(suite)
        padding = self.get_padding(suite.hierarchy_depth)
        suite_label = self.get_suite_label(suite)
        print("%s* %s%s" % (padding, bold(suite_label), " (%s)" % md if md else ""))

        for test in suite.get_tests():
            self.show_test(test, suite)

        for sub_suite in suite.get_suites():
            self.show_suite(sub_suite)

    def show_suites(self, suites):
        for suite in suites:
            self.show_suite(suite)


class ShowCommand(Command):
    def get_name(self):
        return "show"

    def get_description(self):
        return "Show the test tree"

    def add_cli_args(self, cli_parser):
        add_test_filter_cli_args(cli_parser)

        group = cli_parser.add_argument_group("Display")
        group.add_argument(
            "--show-description", "-d", action="store_true",
            help="Show suite and test descriptions instead of paths"
        )

    def run_cmd(self, cli_args):
        project = load_project()
        suites = load_suites_from_project(project, make_test_filter(cli_args))

        renderer = TestTreeRenderer(show_description=cli_args.show_description)
        renderer.show_suites(suites)
        
        return 0
