'''
Created on Feb 14, 2017

@author: nicolas
'''

from __future__ import print_function
from functools import reduce

from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.display import print_table
from lemoncheesecake.cli.utils import filter_testsuites_from_cli_args
from lemoncheesecake.testsuite import add_filter_args_to_cli_parser, walk_testsuites
from lemoncheesecake.project import find_project_file, Project
from lemoncheesecake.exceptions import ProjectError, ProgrammingError

class StatsCommand(Command):
    def get_name(self):
        return "stats"

    def get_description(self):
        return "Display statistics about the project's tests"

    def add_cli_args(self, cli_parser):
        group = cli_parser.add_argument_group("Display")
        self.add_color_cli_args(group)
        add_filter_args_to_cli_parser(cli_parser)

    def run_cmd(self, cli_args):
        self.process_color_cli_args(cli_args)

        project_file = find_project_file()
        if not project_file:
            return "Cannot find project file"
        try:
            project = Project(project_file)
            suites = project.get_testsuites()
        except (ProjectError, ProgrammingError) as e:
            return str(e)

        suites = filter_testsuites_from_cli_args(suites, cli_args)

        class Stats:
            def __init__(self):
                self.tests_nb = 0
                self.testsuites_nb = 0
                self.non_empty_testsuites_nb = 0
                self.tags = {}
                self.properties = {}
                self.links = {}
        stats = Stats()

        def handle_test(test, suite):
            stats.tests_nb += 1
            for tag in test.get_inherited_tags():
                stats.tags[tag] = stats.tags.get(tag, 0) + 1
            for prop, value in test.get_inherited_properties().items():
                if prop not in stats.properties:
                    stats.properties[prop] = {}
                if value not in stats.properties[prop]:
                    stats.properties[prop][value] = 0
                stats.properties[prop][value] += 1
            for link in test.get_inherited_links():
                stats.links[link] = stats.links.get(link, 0) + 1

        def percent_of_tests(val):
            return "%2d%%" % (float(val) / stats.tests_nb * 100)

        def handle_suite(suite):
            stats.testsuites_nb += 1
            if suite.has_selected_tests(deep=False):
                stats.non_empty_testsuites_nb += 1

        walk_testsuites(suites, test_func=handle_test, testsuite_func=handle_suite)

        # Show tags
        lines = []
        for tag in sorted(stats.tags.keys(), key=lambda k: stats.tags[k], reverse=True):
            lines.append([self.bold(tag), stats.tags[tag], percent_of_tests(stats.tags[tag])])
        print_table(self.bold("Tags"), ["Tag", "Tests", "In %"], lines)

        # Show properties
        lines = []
        prop_names = sorted(
            stats.properties.keys(),
            key=lambda k: reduce(lambda x, y: x + y, stats.properties[k].values(), 0),
            reverse=True
        )
        for prop_name in prop_names:
            prop_values = sorted(
                stats.properties[prop_name].keys(),
                key=lambda k: stats.properties[prop_name][k],
                reverse=True
            )
            for prop_value in prop_values:
                lines.append([
                    self.bold(prop_name), self.bold(prop_value),
                    stats.properties[prop_name][prop_value],
                    percent_of_tests(stats.properties[prop_name][prop_value])
                ])
        print_table(self.bold("Properties"), ["Property", "Value", "Tests", "In %"], lines)

        # Show links
        lines = []
        for link in sorted(stats.links.keys(), key=lambda k: stats.links[k], reverse=True):
            lines.append([
                self.bold(link[1] or "-"), link[0], stats.links[link], percent_of_tests(stats.links[link])
            ])
        print_table(self.bold("Links"), ["Name", "URL", "Tests", "In %"], lines)

        summary = "Total: %s in %s" % (
            self.bold("%d tests" % stats.tests_nb),
            self.bold("%d testsuites" % stats.non_empty_testsuites_nb)
        )
        if stats.testsuites_nb > stats.non_empty_testsuites_nb:
            summary += " (+ %d empty suites)" % (stats.testsuites_nb - stats.non_empty_testsuites_nb)
        print(summary)
        print()

        return 0