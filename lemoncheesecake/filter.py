'''
Created on Sep 8, 2016

@author: nicolas
'''

import fnmatch
from functools import reduce

from lemoncheesecake.reporting import load_report
from lemoncheesecake.reporting.reportdir import DEFAULT_REPORT_DIR_NAME
from lemoncheesecake.testtree import flatten_tests
from lemoncheesecake.exceptions import UserError

__all__ = (
    "RunFilter", "ReportFilter", "filter_suites",
    "add_run_filter_cli_args", "make_run_filter", "add_report_filter_cli_args", "make_report_filter"
)

NEGATIVE_FILTER_CHARS = "-^~"


def match_values(values, patterns):
    if not patterns:
        return True

    values = [value or "" for value in values]  # convert None to ""

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
        reduce(lambda x, y: list(x) + list(y), lsts, []),  # make a flat list
        patterns
    )


class Filter(object):
    def is_empty(self):
        raise NotImplemented()

    def is_test_disabled(self, test):
        raise NotImplemented()

    def match_test(self, test):
        raise NotImplemented()


class BaseFilter(Filter):
    def __init__(self, paths=(), descriptions=(), tags=(), properties=(), links=(), enabled=False, disabled=False):
        self.paths = list(paths)
        self.descriptions = list(descriptions)
        self.tags = list(tags)
        self.properties = list(properties)
        self.links = list(links)
        self.enabled = enabled
        self.disabled = disabled

    def is_empty(self):
        return not any([
            self.paths, self.descriptions, self.tags, self.properties, self.links, self.enabled, self.disabled
        ])

    def is_test_disabled(self, test):
        return test.is_disabled()

    def match_test(self, test):
        funcs = [
            lambda: self.is_test_disabled(test) if self.disabled else True,
            lambda: not self.is_test_disabled(test) if self.enabled else True,
            lambda: match_values(test.hierarchy_paths, self.paths),
            lambda: all(match_values(test.hierarchy_descriptions, descs) for descs in self.descriptions),
            lambda: all(match_values(test.hierarchy_tags, tags) for tags in self.tags),
            lambda: all(match_keyvalues(test.hierarchy_properties, props) for props in self.properties),
            lambda: all(match_values_lists(test.hierarchy_links, links) for links in self.links)
        ]
        return all(func() for func in funcs)


class RunFilter(BaseFilter):
    pass


class ReportFilter(RunFilter):
    def __init__(self, statuses=None, **kwargs):
        RunFilter.__init__(self, **kwargs)
        self.statuses = statuses if statuses is not None else set()

    def is_empty(self):
        if not RunFilter.is_empty(self):
            return False

        return len(self.statuses) == 0

    def is_test_disabled(self, test):
        return test.status == "disabled"

    def match_test(self, test):
        if not RunFilter.match_test(self, test):
            return False

        if len(self.statuses) == 0:
            return True

        return test.status in self.statuses


class FromTestsFilter(Filter):
    def __init__(self, tests):
        self.tests = [test.path for test in tests]

    def is_empty(self):
        return False

    def is_test_disabled(self, test):
        return test.status == "disabled"

    def match_test(self, test):
        return test.path in self.tests


def filter_suite(suite, filtr):
    filtered_suite = suite.pull_node()

    for test in suite.get_tests():
        if filtr.match_test(test):
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


def _add_filter_cli_args(cli_parser, no_positional_argument=False, only_executed_tests=False):
    def property_value(value):
        splitted = value.split(":")
        if len(splitted) != 2:
            raise ValueError()
        return splitted

    group = cli_parser.add_argument_group("Filtering")
    if no_positional_argument:
        group.add_argument(
            "--path", "-p", nargs="+", help="Filter on test/suite path (wildcard character '*' can be used)"
        )
    else:
        group.add_argument(
            "path", nargs="*", default=[], help="Filter on test/suite path (wildcard character '*' can be used)"
        )
    group.add_argument(
        "--desc", nargs="+", action="append", default=[], help="Filter on descriptions"
    )
    group.add_argument(
        "--tag", "-a", nargs="+", action="append", default=[], help="Filter on tags"
    )
    group.add_argument(
        "--property", "-m", nargs="+", type=property_value, action="append", default=[], help="Filter on properties"
    )
    group.add_argument(
        "--link", "-l", nargs="+", action="append", default=[], help="Filter on links (names and URLs)"
    )
    group.add_argument(
        "--passed", action="store_true", help="Filter on passed tests (implies/triggers --from-report)"
    )
    group.add_argument(
        "--failed", action="store_true", help="Filter on failed tests (implies/triggers --from-report)"
    )
    if not only_executed_tests:
        group.add_argument(
            "--skipped", action="store_true", help="Filter on skipped tests (implies/triggers --from-report)"
        )
        group.add_argument(
            "--non-passed", action="store_true", help="Alias for --failed --skipped"
        )
        group.add_argument(
            "--disabled", action="store_true", help="Filter on disabled tests"
        )
        group.add_argument(
            "--enabled", action="store_true", help="Filter on enabled (non-disabled) tests"
        )
    group.add_argument(
        "--from-report", required=False, help="When enabled, the filtering is based on the given report"
    )

    return group


def add_run_filter_cli_args(cli_parser):
    return _add_filter_cli_args(cli_parser)


def add_report_filter_cli_args(cli_parser, only_executed_tests=False):
    return _add_filter_cli_args(cli_parser, no_positional_argument=True, only_executed_tests=only_executed_tests)


def _set_base_filter(fltr, cli_args, only_executed_tests=False):
    if not only_executed_tests and (cli_args.disabled and cli_args.enabled):
        raise UserError("--disabled and --enabled arguments are mutually exclusive")

    fltr.paths = cli_args.path
    fltr.descriptions = cli_args.desc
    fltr.tags = cli_args.tag
    fltr.properties = cli_args.property
    fltr.links = cli_args.link
    if not only_executed_tests:
        fltr.disabled = cli_args.disabled
        fltr.enabled = cli_args.enabled


def _set_run_filter(filtr, cli_args):
    if cli_args.passed or cli_args.failed or cli_args.skipped:
        raise UserError("--passed, --failed and --skipped arguments can only be used on the report-based filter")
    _set_base_filter(filtr, cli_args)


def _make_run_filter(cli_args):
    fltr = RunFilter()
    _set_run_filter(fltr, cli_args)
    return fltr


def _make_report_filter(cli_args, only_executed_tests=False):
    fltr = ReportFilter()
    _set_base_filter(fltr, cli_args, only_executed_tests=only_executed_tests)

    if only_executed_tests:
        if cli_args.passed:
            fltr.statuses.add("passed")
        if cli_args.failed:
            fltr.statuses.add("failed")
        # when neither --passed not --failed was passed, enforce statuses passed and failed
        # to select tests that have been executed
        if len(fltr.statuses) == 0:
            fltr.statuses.update(("passed", "failed"))
    else:
        if cli_args.passed:
            fltr.statuses.add("passed")
        if cli_args.failed:
            fltr.statuses.add("failed")
        if cli_args.skipped:
            fltr.statuses.add("skipped")
        if cli_args.non_passed:
            fltr.statuses.update(("failed", "skipped"))

    return fltr


def _make_from_report_filter(cli_args, only_executed_tests=False):
    report = load_report(cli_args.from_report or DEFAULT_REPORT_DIR_NAME)
    filtr = _make_report_filter(cli_args, only_executed_tests=only_executed_tests)
    suites = filter_suites(report.get_suites(), filtr)
    return FromTestsFilter(flatten_tests(suites))


def make_run_filter(cli_args):
    if any([cli_args.from_report, cli_args.passed, cli_args.failed, cli_args.skipped]):
        return _make_from_report_filter(cli_args)
    else:
        return _make_run_filter(cli_args)


def make_report_filter(cli_args, only_executed_tests=False):
    if cli_args.from_report:
        return _make_from_report_filter(cli_args, only_executed_tests=only_executed_tests)
    else:
        return _make_report_filter(cli_args, only_executed_tests=only_executed_tests)
