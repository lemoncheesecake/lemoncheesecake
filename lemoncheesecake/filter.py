'''
Created on Sep 8, 2016

@author: nicolas
'''

import re
import fnmatch
from functools import reduce

from lemoncheesecake.reporting import load_report
from lemoncheesecake.reporting.reportdir import DEFAULT_REPORT_DIR_NAME
from lemoncheesecake.reporting.report import Result, TestResult, Log, Check, Attachment, Url
from lemoncheesecake.testtree import flatten_tests, BaseTest, BaseSuite
from lemoncheesecake.exceptions import UserError
from lemoncheesecake.consts import NEGATIVE_CHARS


class Filter(object):
    def __bool__(self):
        raise NotImplemented()

    def __nonzero__(self):  # for Python 2 compatibility
        return self.__bool__()

    def __call__(self, test):
        raise NotImplemented()


class BaseFilter(Filter):
    def __init__(self, paths=(), descriptions=(), tags=(), properties=(), links=()):
        self.paths = list(paths)
        self.descriptions = list(descriptions)
        self.tags = list(tags)
        self.properties = list(properties)
        self.links = list(links)

    def __bool__(self):
        return any((
            self.paths, self.descriptions, self.tags, self.properties, self.links
        ))

    @staticmethod
    def _match_values(values, patterns):
        if not patterns:
            return True

        values = [value or "" for value in values]  # convert None to ""

        for pattern in patterns:
            if pattern[0] in NEGATIVE_CHARS:
                if not fnmatch.filter(values, pattern[1:]):
                    return True
            else:
                if fnmatch.filter(values, pattern):
                    return True
        return False

    @staticmethod
    def _match_key_values(key_values, patterns):
        if not patterns:
            return True

        for key, value in patterns:
            if key in key_values:
                if value[0] in NEGATIVE_CHARS:
                    if not fnmatch.fnmatch(key_values[key], value[1:]):
                        return True
                else:
                    if fnmatch.fnmatch(key_values[key], value):
                        return True
        return False

    @staticmethod
    def _match_values_lists(lsts, patterns):
        return BaseFilter._match_values(
            reduce(lambda x, y: list(x) + list(y), lsts, []),  # make a flat list
            patterns
        )

    def _do_paths(self, node):
        return self._match_values(node.hierarchy_paths, self.paths)

    def _do_descriptions(self, node):
        return all(self._match_values(node.hierarchy_descriptions, descs) for descs in self.descriptions)

    def _do_tags(self, node):
        return all(self._match_values(node.hierarchy_tags, tags) for tags in self.tags)

    def _do_properties(self, node):
        return all(self._match_key_values(node.hierarchy_properties, props) for props in self.properties)

    def _do_links(self, node):
        return all(self._match_values_lists(node.hierarchy_links, links) for links in self.links)

    @staticmethod
    def _apply_criteria(obj, *criteria):
        return all(criterion(obj) for criterion in criteria)

    def __call__(self, node):
        assert isinstance(node, (BaseTest, BaseSuite))
        return self._apply_criteria(
            node, self._do_paths, self._do_descriptions, self._do_tags, self._do_properties, self._do_links
        )


class RunFilter(BaseFilter):
    def __init__(self, enabled=False, disabled=False, **kwargs):
        BaseFilter.__init__(self, **kwargs)
        self.enabled = enabled
        self.disabled = disabled

    def __bool__(self):
        return BaseFilter.__bool__(self) or any((self.enabled, self.disabled))

    def _do_enabled(self, node):
        return not node.is_disabled() if self.enabled else True

    def _do_disabled(self, node):
        return node.is_disabled() if self.disabled else True

    def _apply_run_criteria(self, node):
        return self._apply_criteria(node, self._do_enabled, self._do_disabled)

    def __call__(self, node):
        return BaseFilter.__call__(self, node) and self._apply_run_criteria(node)


class ReportFilter(BaseFilter):
    def __init__(self, statuses=None, enabled=False, disabled=False, grep=None, **kwargs):
        BaseFilter.__init__(self, **kwargs)
        self.statuses = set(statuses) if statuses is not None else set()
        self.enabled = enabled
        self.disabled = disabled
        self.grep = grep

    def __bool__(self):
        return BaseFilter.__bool__(self) or any((self.statuses, self.enabled, self.disabled, self.grep))

    def _do_statuses(self, result):
        return result.status in self.statuses if self.statuses else True

    def _do_enabled(self, result):
        return result.status != "disabled" if self.enabled else True

    def _do_disabled(self, result):
        return result.status == "disabled" if self.disabled else True

    @staticmethod
    def _iter_grepable(result):
        for step in result.steps:
            yield step.description
            for entry in step.entries:
                if isinstance(entry, Log):
                    yield entry.message
                elif isinstance(entry, Check):
                    yield entry.description
                    if entry.details:
                        yield entry.details
                elif isinstance(entry, Attachment):
                    yield entry.filename
                    yield entry.description
                elif isinstance(entry, Url):
                    yield entry.url
                    yield entry.description

    def _do_grep(self, result):
        if not self.grep:
            return True

        return any(map(self.grep.search, self._iter_grepable(result)))

    def _apply_report_criteria(self, result):
        return self._apply_criteria(
            result, self._do_statuses, self._do_enabled, self._do_disabled, self._do_grep
        )

    def __call__(self, result):
        # type: (Result) -> bool

        assert isinstance(result, Result)

        # test result:
        if isinstance(result, TestResult):
            return BaseFilter.__call__(self, result) and self._apply_report_criteria(result)
        # suite setup or teardown result, apply the base filter on the suite node:
        elif result.parent_suite:
            return BaseFilter.__call__(self, result.parent_suite) and self._apply_report_criteria(result)
        # session setup or teardown:
        else:
            if BaseFilter.__bool__(self):
                # no criteria of BaseFilter is applicable to a session setup/teardown result,
                # meaning it's a no match
                return False
            else:
                return self._apply_report_criteria(result)


class FromTestsFilter(Filter):
    def __init__(self, tests):
        self._tests = [test.path for test in tests]

    def __bool__(self):
        return True

    def __call__(self, test):
        return test.path in self._tests


def filter_suite(suite, filtr):
    filtered_suite = suite.pull_node()

    for test in suite.get_tests():
        if filtr(test):
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
    group.add_argument(
        "--grep", "-g", help="Filter result content using pattern (implies/triggers --from-report)"
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


def _set_common_filter_criteria(fltr, cli_args, only_executed_tests=False):
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


def _set_run_filter_criteria(filtr, cli_args):
    if cli_args.passed or cli_args.failed or cli_args.skipped:
        raise UserError("--passed, --failed and --skipped arguments can only be used on the report-based filter")
    _set_common_filter_criteria(filtr, cli_args)


def _make_run_filter(cli_args):
    fltr = RunFilter()
    _set_run_filter_criteria(fltr, cli_args)
    return fltr


def _make_report_filter(cli_args, only_executed_tests=False):
    fltr = ReportFilter()
    _set_common_filter_criteria(fltr, cli_args, only_executed_tests=only_executed_tests)

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

    if cli_args.grep:
        fltr.grep = re.compile(cli_args.grep, re.IGNORECASE | re.MULTILINE)

    return fltr


def _make_from_report_filter(cli_args, only_executed_tests=False):
    report = load_report(cli_args.from_report or DEFAULT_REPORT_DIR_NAME)
    filtr = _make_report_filter(cli_args, only_executed_tests=only_executed_tests)
    suites = filter_suites(report.get_suites(), filtr)
    return FromTestsFilter(flatten_tests(suites))


def make_run_filter(cli_args):
    if any((cli_args.from_report, cli_args.passed, cli_args.failed, cli_args.skipped, cli_args.grep)):
        return _make_from_report_filter(cli_args)
    else:
        return _make_run_filter(cli_args)


def make_report_filter(cli_args, only_executed_tests=False):
    if cli_args.from_report:
        return _make_from_report_filter(cli_args, only_executed_tests=only_executed_tests)
    else:
        return _make_report_filter(cli_args, only_executed_tests=only_executed_tests)
