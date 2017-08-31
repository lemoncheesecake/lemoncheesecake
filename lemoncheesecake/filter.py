'''
Created on Sep 8, 2016

@author: nicolas
'''

import fnmatch
from functools import reduce

__all__ = ("Filter", "ReportFilter", "filter_suites", "add_filter_args_to_cli_parser", "make_filter_from_cli_args")

NEGATIVE_FILTER_CHARS = "-^~"


def match_values(values, patterns):
    if not patterns:
        return True

    values = [value or "" for value in values] # convert None to ""

    for pattern in patterns:
        if pattern[0] in NEGATIVE_FILTER_CHARS:
            if not fnmatch.filter(values, pattern[1:]):
                return True
        else:
            if fnmatch.filter(values, pattern):
                return True
    return False


def match_keyvalues(keyvalues, patterns):
    if not patterns:
        return True

    for key, value in patterns:
        if key in keyvalues:
            if value[0] in NEGATIVE_FILTER_CHARS:
                if not fnmatch.fnmatch(keyvalues[key], value[1:]):
                    return True
            else:
                if fnmatch.fnmatch(keyvalues[key], value):
                    return True
    return False


def match_values_lists(lsts, patterns):
    return match_values(
        reduce(lambda x, y: list(x) + list(y), lsts, []), # make a flat list
        patterns
    )


class Filter:
    def __init__(self):
        self.paths = []
        self.descriptions = []
        self.tags = [ ]
        self.properties = []
        self.links = [ ]

    def is_empty(self):
        return not any([self.paths, self.descriptions, self.tags, self.properties, self.links])

    def match_test(self, test, suite):
        funcs = [
            lambda: match_values(test.get_inherited_paths(), self.paths),
            lambda: all(match_values(test.get_inherited_descriptions(), descs) for descs in self.descriptions),
            lambda: all(match_values(test.get_inherited_tags(), tags) for tags in self.tags),
            lambda: all(match_keyvalues(test.get_inherited_properties(), props) for props in self.properties),
            lambda: all(match_values_lists(test.get_inherited_links(), links) for links in self.links)
        ]
        return all(func() for func in funcs)


class ReportFilter(Filter):
    def __init__(self):
        Filter.__init__(self)
        self.statuses = []

    def is_empty(self):
        if not Filter.is_empty(self):
            return False

        return len(self.statuses) == 0

    def match_test(self, test, suite):
        if not Filter.match_test(self, test, suite):
            return False

        if len(self.statuses) == 0:
            return True

        return test.status in self.statuses


def filter_suite(suite, filtr):
    filtered_suite = suite.pull_node()

    for test in suite.get_tests():
        if filtr.match_test(test, suite):
            filtered_suite.add_test(test.pull_node())

    for filtered_sub_suite in filter_suites(suite.get_suites(), filtr):
        filtered_suite.add_suite(filtered_sub_suite)

    return filtered_suite


def filter_suites(suites, filtr):
    filtered_suites = []

    for suite in suites:
        filtered_suite = filter_suite(suite, filtr)
        if not filtered_suite.is_empty():
            filtered_suites.append(filtered_suite)

    return filtered_suites


def add_filter_args_to_cli_parser(cli_parser):
    def property_value(value):
        splitted = value.split(":")
        if len(splitted) != 2:
            raise ValueError()
        return splitted

    group = cli_parser.add_argument_group("Filtering")
    group.add_argument("path", nargs="*", default=[], help="Filter on test/suite path (wildcard character '*' can be used)")
    group.add_argument("--desc", nargs="+", action="append", default=[], help="Filter on descriptions")
    group.add_argument("--tag", "-a", nargs="+", action="append", default=[], help="Filter on tags")
    group.add_argument("--property", "-m", nargs="+", type=property_value, action="append", default=[], help="Filter on properties")
    group.add_argument("--link", "-l", nargs="+", action="append", default=[], help="Filter on links (names and URLs)")

    return group


def add_report_filter_args_to_cli_parser(cli_parser):
    group = add_filter_args_to_cli_parser(cli_parser)
    group.add_argument("--passed", action="store_true", help="Filter on passed test")
    group.add_argument("--failed", action="store_true", help="Filter on failed test")
    group.add_argument("--skipped", action="store_true", help="Filter on skipped test")
    group.add_argument("--disabled", action="store_true", help="Filter on disabled test")


def _set_filter_from_cli_args(fltr, cli_args):
    fltr.paths = cli_args.path
    fltr.descriptions = cli_args.desc
    fltr.tags = cli_args.tag
    fltr.properties = cli_args.property
    fltr.links = cli_args.link
    return fltr


def make_filter_from_cli_args(cli_args):
    fltr = Filter()
    _set_filter_from_cli_args(fltr, cli_args)
    return fltr


def make_report_filter_from_cli_args(cli_args):
    fltr = ReportFilter()
    _set_filter_from_cli_args(fltr, cli_args)

    if cli_args.passed:
        fltr.statuses.append("passed")
    if cli_args.failed:
        fltr.statuses.append("failed")
    if cli_args.skipped:
        fltr.statuses.append("skipped")
    if cli_args.disabled:
        fltr.statuses.append("disabled")

    return fltr
