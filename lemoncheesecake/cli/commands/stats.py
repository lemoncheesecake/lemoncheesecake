'''
Created on Feb 14, 2017

@author: nicolas
'''

from __future__ import print_function
from functools import reduce

from lemoncheesecake.helpers.console import print_table, bold
from lemoncheesecake.cli.command import Command
from lemoncheesecake.cli.utils import load_suites_from_project
from lemoncheesecake.filter import add_test_filter_cli_args, make_test_filter
from lemoncheesecake.testtree import flatten_suites
from lemoncheesecake.project import load_project


class Stats:
    def __init__(self):
        self.tests_nb = 0
        self.disabled_tests_nb = 0
        self.suites_nb = 0
        self.non_empty_suites_nb = 0
        self.tags = {}
        self.properties = {}
        self.links = {}


def compute_stats(suites):
    stats = Stats()

    for suite in flatten_suites(suites):
        stats.suites_nb += 1
        for test in suite.get_tests():
            stats.tests_nb += 1
            if test.is_disabled():
                stats.disabled_tests_nb += 1
            for tag in test.hierarchy_tags:
                stats.tags[tag] = stats.tags.get(tag, 0) + 1
            for prop, value in test.hierarchy_properties.items():
                if prop not in stats.properties:
                    stats.properties[prop] = {}
                if value not in stats.properties[prop]:
                    stats.properties[prop][value] = 0
                stats.properties[prop][value] += 1
            for link in test.hierarchy_links:
                stats.links[link] = stats.links.get(link, 0) + 1
        else:
            stats.non_empty_suites_nb += 1

    return stats


class StatsCommand(Command):
    def get_name(self):
        return "stats"

    def get_description(self):
        return "Display statistics about the project's tests"

    def add_cli_args(self, cli_parser):
        add_test_filter_cli_args(cli_parser)

    def run_cmd(self, cli_args):
        project = load_project()
        suites = load_suites_from_project(project, make_test_filter(cli_args))

        stats = compute_stats(suites)

        def percent_of_tests(val):
            return "%2d%%" % (float(val) / stats.tests_nb * 100)

        # Show tags
        lines = []
        for tag in sorted(stats.tags.keys(), key=lambda k: stats.tags[k], reverse=True):
            lines.append([bold(tag), stats.tags[tag], percent_of_tests(stats.tags[tag])])
        print_table(bold("Tags"), ["Tag", "Tests", "In %"], lines)

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
                    bold(prop_name), bold(prop_value),
                    stats.properties[prop_name][prop_value],
                    percent_of_tests(stats.properties[prop_name][prop_value])
                ])
        print_table(bold("Properties"), ["Property", "Value", "Tests", "In %"], lines)

        # Show links
        lines = []
        for link in sorted(stats.links.keys(), key=lambda k: stats.links[k], reverse=True):
            lines.append([
                bold(link[1] or "-"), link[0], stats.links[link], percent_of_tests(stats.links[link])
            ])
        print_table(bold("Links"), ["Name", "URL", "Tests", "In %"], lines)

        tests_info = bold("%d tests" % stats.tests_nb)
        if stats.disabled_tests_nb > 0:
            tests_info += " (among which %s disabled tests)" % stats.disabled_tests_nb

        suites_info = bold("%d suites" % stats.non_empty_suites_nb)
        if stats.suites_nb > stats.non_empty_suites_nb:
            suites_info += " (+ %d empty suites)" % (stats.suites_nb - stats.non_empty_suites_nb)

        print("Total: %s in %s" % (tests_info, suites_info))
        print()

        return 0
