'''
Created on Mar 26, 2016

@author: nicolas
'''

import time
from decimal import Decimal
from functools import reduce
from typing import Union, List, Iterable, Optional
import datetime
import calendar

from typing import Callable, Any

from lemoncheesecake.helpers.time import humanize_duration
from lemoncheesecake.testtree import BaseTest, BaseSuite, flatten_tests, flatten_suites, find_test, find_suite, \
    filter_suites, normalize_node_hierarchy, TreeNodeHierarchy

LOG_LEVEL_DEBUG = "debug"
LOG_LEVEL_INFO = "info"
LOG_LEVEL_WARN = "warn"
LOG_LEVEL_ERROR = "error"

_TEST_STATUSES = "passed", "failed", "skipped", "disabled"
_DEFAULT_REPORT_TITLE = "Test Report"


# NB: it would be nicer to use:
# datetime.isoformat(sep=' ', timespec='milliseconds')
# unfortunately, the timespec argument is only available since Python 3.6
def format_time_as_iso8601(ts):
    # type: (float) -> str
    """
    Serialize time as ISO8601, such as: "2019-05-04T22:57:08.399Z"
    """
    ts = round(ts, 3)  # round the timestamp to milliseconds
    result = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ts))  # builds datetime with second precision
    result += ".%03d" % (Decimal(repr(ts)) % 1 * 1000)  # adds millisecond precision
    result += "Z"  # declares as UTC
    return result


def parse_iso8601_time(s):
    # type: (str) -> float
    """
    Parse time as generated by format_time_as_iso8601
    """
    dt = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ")
    return calendar.timegm(dt.utctimetuple()) + float(dt.microsecond) / 1000000


def _get_duration(start_time, end_time):
    # type: (Optional[float], Optional[float]) -> Optional[float]
    if start_time is not None and end_time is not None:
        return end_time - start_time
    else:
        return None


class StepLog(object):
    def __init__(self, ts):
        self.time = ts


class Log(StepLog):
    def __init__(self, level, message, ts):
        # type: (str, str, float) -> None
        super(Log, self).__init__(ts)
        self.level = level
        self.message = message


class Check(StepLog):
    def __init__(self, description, is_successful, details, ts):
        # type: (str, bool, Optional[str], float) -> None
        super(Check, self).__init__(ts)
        self.description = description
        self.is_successful = is_successful
        self.details = details


class Attachment(StepLog):
    def __init__(self, description, filename, as_image, ts):
        # type: (str, str, bool, float) -> None
        super(Attachment, self).__init__(ts)
        self.description = description
        self.filename = filename
        self.as_image = as_image


class Url(StepLog):
    def __init__(self, description, url, ts):
        # type: (str, str, float) -> None
        super(Url, self).__init__(ts)
        self.description = description
        self.url = url


class Step(object):
    def __init__(self, description):
        # type: (str) -> None
        self.description = description
        self.parent_result = None
        self.entries = []  # type: List[Union[Log, Check, Attachment, Url]]
        self.start_time = None  # type: Optional[float]
        self.end_time = None  # type: Optional[float]

    @staticmethod
    def _is_entry_successful(entry):
        if isinstance(entry, Check):
            return entry.is_successful
        elif isinstance(entry, Log):
            return entry.level != LOG_LEVEL_ERROR
        return True

    def is_successful(self):
        # type: () -> bool
        return all(map(Step._is_entry_successful, self.entries))

    @property
    def duration(self):
        # type: () -> Optional[float]
        return _get_duration(self.start_time, self.end_time)


class Result(object):
    def __init__(self):
        # please note that this attribute is also defined in TestResult through BaseTest,
        # one will override the other
        self.parent_suite = None  # type: Optional[SuiteResult]
        self.type = None  # type: Optional[str]
        self._steps = []  # type: List[Step]
        self.start_time = None  # type: Optional[float]
        self.end_time = None  # type: Optional[float]
        self.status = None  # type: Optional[str]
        self.status_details = None  # type: Optional[str]

    def add_step(self, step):
        # type: (Step) -> None
        step.parent_result = self
        self._steps.append(step)

    def get_steps(self):
        # type: () -> List[Step]
        return self._steps

    def is_successful(self):
        # type: () -> bool
        if self.status:  # test is finished
            return self.status in ("passed", "disabled")
        else:  # check if the test is successful "so far"
            return all(step.is_successful() for step in self._steps)

    @property
    def duration(self):
        # type: () -> Optional[float]
        return _get_duration(self.start_time, self.end_time)


class TestResult(BaseTest, Result):
    def __init__(self, name, description):
        BaseTest.__init__(self, name, description)
        Result.__init__(self)
        # non-serialized attributes (only set in-memory during test execution):
        self.rank = 0


class SuiteResult(BaseSuite):
    def __init__(self, name, description):
        BaseSuite.__init__(self, name, description)
        self.start_time = None  # type: Optional[float]
        self.end_time = None  # type: Optional[float]
        self._suite_setup = None  # type: Optional[Result]
        self._suite_teardown = None  # type: Optional[Result]
        # non-serialized attributes (only set in-memory during test execution)
        self.rank = 0

    @property
    def suite_setup(self):
        return self._suite_setup
    
    @suite_setup.setter
    def suite_setup(self, setup):
        if setup:
            setup.parent_suite = self
            setup.type = "suite_setup"
        self._suite_setup = setup

    @property
    def suite_teardown(self):
        return self._suite_teardown

    @suite_teardown.setter
    def suite_teardown(self, teardown):
        if teardown:
            teardown.parent_suite = self
            teardown.type = "suite_teardown"
        self._suite_teardown = teardown

    @property
    def duration(self):
        # type: () -> Optional[float]
        return reduce(
            lambda x, y: x + y,
            # result.duration is None if the corresponding result is in progress
            [result.duration or 0 for result in flatten_results([self])],
            0
        )

    def get_tests(self):
        # type: () -> List[TestResult]
        tests = super(SuiteResult, self).get_tests()
        return sorted(tests, key=lambda t: t.rank)

    def get_suites(self, include_empty_suites=False):
        # type: (bool) -> List[SuiteResult]
        suites = super(SuiteResult, self).get_suites(include_empty_suites)
        return sorted(suites, key=lambda s: s.rank)

    def pull_node(self):
        node = BaseSuite.pull_node(self)
        node._suite_setup = None
        node._suite_teardown = None
        return node

    def is_empty(self):
        return BaseSuite.is_empty(self) and self._suite_setup is None and self._suite_teardown is None

    def filter(self, result_filter):
        suite = BaseSuite.filter(self, result_filter)
        if self._suite_setup and result_filter(self._suite_setup):
            suite._suite_setup = self._suite_setup
        if self._suite_teardown and result_filter(self._suite_teardown):
            suite._suite_teardown = self._suite_teardown
        return suite


class ReportLocation(object):
    _TEST_SESSION_SETUP = 0
    _TEST_SESSION_TEARDOWN = 1
    _SUITE_SETUP = 2
    _SUITE_TEARDOWN = 3
    _TEST = 4

    def __init__(self, node_type, node_hierarchy=None):
        self.node_type = node_type
        self.node_hierarchy = node_hierarchy

    @classmethod
    def in_test_session_setup(cls):
        # type: () -> ReportLocation
        return cls(cls._TEST_SESSION_SETUP)

    @classmethod
    def in_test_session_teardown(cls):
        # type: () -> ReportLocation
        return cls(cls._TEST_SESSION_TEARDOWN)

    @classmethod
    def in_suite_setup(cls, suite):
        # type: (TreeNodeHierarchy) -> ReportLocation
        return cls(cls._SUITE_SETUP, normalize_node_hierarchy(suite))

    @classmethod
    def in_suite_teardown(cls, suite):
        # type: (TreeNodeHierarchy) -> ReportLocation
        return cls(cls._SUITE_TEARDOWN, normalize_node_hierarchy(suite))

    @classmethod
    def in_test(cls, test):
        # type: (TreeNodeHierarchy) -> ReportLocation
        return cls(cls._TEST, normalize_node_hierarchy(test))

    def get(self, report):
        # type: (Report) -> Union[Result, SuiteResult, TestResult, None]
        if self.node_type == self._TEST_SESSION_SETUP:
            return report.test_session_setup
        elif self.node_type == self._TEST_SESSION_TEARDOWN:
            return report.test_session_teardown
        elif self.node_type == self._SUITE_SETUP:
            suite = report.get_suite(self.node_hierarchy)
            return suite.suite_setup
        elif self.node_type == self._SUITE_TEARDOWN:
            suite = report.get_suite(self.node_hierarchy)
            return suite.suite_teardown
        elif self.node_type == self._TEST:
            return report.get_test(self.node_hierarchy)
        else:
            raise Exception("Unknown self type %s" % self.node_type)

    def __eq__(self, other):
        return all((
            isinstance(other, ReportLocation),
            self.node_type == other.node_type,
            self.node_hierarchy == other.node_hierarchy
        ))

    def __hash__(self):
        return hash((self.node_type, self.node_hierarchy))

    def __str__(self):
        ret = ""
        if self.node_hierarchy:
            ret += ".".join(self.node_hierarchy) + " "
        ret += ("session setup", "session teardown", "suite setup", "suite teardown", "test")[self.node_type]
        return "<%s>" % ret


def flatten_results(suites):
    # type: (Iterable[SuiteResult]) -> Iterable[Result]
    for suite in flatten_suites(suites):
        if suite.suite_setup:
            yield suite.suite_setup
        for test in suite.get_tests():
            yield test
        if suite.suite_teardown:
            yield suite.suite_teardown


class Report(object):
    def __init__(self):
        self.info = []
        self._test_session_setup = None  # type: Optional[Result]
        self._test_session_teardown = None  # type: Optional[Result]
        self._suites = []  # type: List[SuiteResult]
        self.start_time = None  # type: Optional[float]
        self.end_time = None  # type: Optional[float]
        self.report_generation_time = None  # type: Optional[float]
        self.title = _DEFAULT_REPORT_TITLE
        self.nb_threads = 1

    @property
    def test_session_setup(self):
        return self._test_session_setup

    @test_session_setup.setter
    def test_session_setup(self, setup):
        if setup:
            setup.type = "test_session_setup"
        self._test_session_setup = setup

    @property
    def test_session_teardown(self):
        return self._test_session_teardown

    @test_session_teardown.setter
    def test_session_teardown(self, teardown):
        if teardown:
            teardown.type = "test_session_teardown"
        self._test_session_teardown = teardown

    @property
    def duration(self):
        # type: () -> Optional[float]
        return _get_duration(self.start_time, self.end_time)

    @property
    def nb_tests(self):
        # type: () -> int
        return len(list(self.all_tests()))

    @property
    def parallelized(self):
        # type: () -> bool
        return self.nb_threads > 1 and self.nb_tests > 1

    def add_info(self, name, value):
        # type: (str, str) -> None
        self.info.append([name, value])
    
    def add_suite(self, suite):
        # type: (SuiteResult) -> None
        self._suites.append(suite)
    
    def get_suites(self):
        # type: () -> List[SuiteResult]
        return sorted(self._suites, key=lambda s: s.rank)

    def get_suite(self, hierarchy):
        # type: (List[str]) -> SuiteResult
        return find_suite(self._suites, hierarchy)

    def get_test(self, hierarchy):
        # type: (List[str]) -> TestResult
        return find_test(self._suites, hierarchy)

    def get(self, location):
        # type: (ReportLocation) -> Union[Result, SuiteResult, TestResult, None]
        return location.get(self)

    def is_successful(self):
        # type: () -> bool
        return all(result.status in ("passed", "disabled") for result in self.all_results())

    def all_suites(self, result_filter=None):
        # type: (Optional[Callable[[TestResult], bool]]) -> Iterable[SuiteResult]
        if result_filter:
            return flatten_suites(filter_suites(self._suites, result_filter))
        else:
            return flatten_suites(self._suites)

    def all_tests(self):
        # type: () -> Iterable[TestResult]
        return flatten_tests(self._suites)

    def all_results(self):
        # type: () -> Iterable[Result]
        if self.test_session_setup:
            yield self.test_session_setup
        for result in flatten_results(self.get_suites()):
            yield result
        if self.test_session_teardown:
            yield self.test_session_teardown

    def all_steps(self):
        # type: () -> Iterable[Step]
        for result in self.all_results():
            for step in result.get_steps():
                yield step

    def build_message(self, template):
        stats = ReportStats.from_report(self)
        variables = {
            name: func(self, stats) for name, func in _report_message_variables.items()
        }
        return template.format(**variables)


class ReportStats(object):
    def __init__(self):
        self.tests_nb = 0
        self.tests_nb_by_status = {s: 0 for s in _TEST_STATUSES}
        self.duration = None
        self.duration_cumulative = 0

    @property
    def tests_enabled_nb(self):
        return sum((self.tests_nb_by_status["passed"], self.tests_nb_by_status["failed"], self.tests_nb_by_status["skipped"]))

    @property
    def successful_tests_percentage(self):
        return (float(self.tests_nb_by_status["passed"]) / self.tests_enabled_nb * 100) if self.tests_enabled_nb else 0

    @property
    def duration_cumulative_description(self):
        description = humanize_duration(self.duration_cumulative)
        if self.duration:
            description += " (parallelization speedup factor is %.1f)" % (float(self.duration_cumulative) / self.duration)
        return description

    @classmethod
    def from_results(cls, results, duration):
        # type: (List[Result], Any[int, None]) -> ReportStats

        stats = cls()

        stats.duration = duration

        stats.duration_cumulative = sum(result.duration or 0 for result in results)

        tests = list(filter(lambda r: isinstance(r, TestResult), results))

        stats.tests_nb = len(tests)

        for test in tests:
            if test.status:
                stats.tests_nb_by_status[test.status] += 1

        return stats

    @classmethod
    def from_report(cls, report):
        # type: (Report) -> ReportStats
        return cls.from_results(list(report.all_results()), report.duration)

    @classmethod
    def from_suites(cls, suites, parallelized):
        # type: (List[SuiteResult], bool) -> ReportStats
        results = list(flatten_results(suites))

        return cls.from_results(
            results,
            results[-1].end_time - results[0].start_time if not parallelized else None
        )


def _percent(val, of):
    return "%d%%" % ((float(val) / of * 100) if of else 0)


_report_message_variables = {
    "start_time": lambda report, stats: time.asctime(time.localtime(report.start_time)),
    "end_time": lambda report, stats: time.asctime(time.localtime(report.end_time)),
    "duration": lambda report, stats: humanize_duration(report.end_time - report.start_time),

    "total": lambda report, stats: stats.tests_nb,
    "enabled": lambda report, stats: stats.tests_enabled_nb,

    "passed": lambda report, stats: stats.tests_nb_by_status["passed"],
    "passed_pct": lambda report, stats: _percent(stats.tests_nb_by_status["passed"], of=stats.tests_enabled_nb),

    "failed": lambda report, stats: stats.tests_nb_by_status["failed"],
    "failed_pct": lambda report, stats: _percent(stats.tests_nb_by_status["failed"], of=stats.tests_enabled_nb),

    "skipped": lambda report, stats: stats.tests_nb_by_status["skipped"],
    "skipped_pct": lambda report, stats: _percent(stats.tests_nb_by_status["skipped"], of=stats.tests_enabled_nb),

    "disabled": lambda report, stats: stats.tests_nb_by_status["disabled"],
    "disabled_pct": lambda report, stats: _percent(stats.tests_nb_by_status["disabled"], of=stats.tests_nb)
}


def check_report_message_template(template):
    try:
        template.format(**{name: "" for name in _report_message_variables})
        return template
    except KeyError as excp:
        raise ValueError("invalid report message template, unknown variable: %s" % excp)
