'''
Created on Mar 26, 2016

@author: nicolas
'''

from __future__ import annotations

import time
from functools import reduce
from typing import Union, List, Iterator, Iterable, Optional, Callable
from datetime import datetime, timezone

from lemoncheesecake.helpers.time import humanize_duration
from lemoncheesecake.testtree import BaseTest, BaseSuite, flatten_tests, flatten_suites, find_test, find_suite, \
    normalize_node_hierarchy, TreeNodeHierarchy
from lemoncheesecake.reporting.backend import ReportSerializerMixin


def format_time_as_iso8601(ts: float) -> str:
    """
    Serialize time as ISO8601, such as: "2019-05-04T22:57:08.399Z"
    """
    ts = round(ts, 3)  # round the timestamp to milliseconds
    dt = datetime.utcfromtimestamp(ts)
    return dt.isoformat(timespec='milliseconds') + "Z"


def parse_iso8601_time(s: str) -> float:
    """
    Parse time as generated by format_time_as_iso8601
    """
    dt = datetime.fromisoformat(s.rstrip("Z"))
    return dt.replace(tzinfo=timezone.utc).timestamp()


def _get_duration(start_time: Optional[float], end_time: Optional[float]) -> Optional[float]:
    if start_time is not None and end_time is not None:
        return end_time - start_time
    else:
        return None


class StepLog:
    """
    Base class for logs contained in a Step instance.
    """
    def __init__(self, ts: float) -> None:
        #: Log time.
        self.time: float = ts
        #: Parent step.
        self.parent_step: Optional[Step] = None


class Log(StepLog):
    """
    The log resulting of log_info/log_debug/log_warning/log_error functions.
    Inherits :py:class:`StepLog <lemoncheesecake.reporting.StepLog>`.
    """
    LEVEL_DEBUG = "debug"
    LEVEL_INFO = "info"
    LEVEL_WARN = "warn"
    LEVEL_ERROR = "error"

    def __init__(self, level: str, message: str, ts: float) -> None:
        super().__init__(ts)
        #: Log level.
        self.level: str = level
        #: Log message.
        self.message: str = message


class Check(StepLog):
    """
    The log resulting of a check_that/require_that/assert_that functions.
    Inherits :py:class:`StepLog <lemoncheesecake.reporting.StepLog>`.
    """
    def __init__(self, description: str, is_successful: bool, details: Optional[str], ts: float) -> None:
        super().__init__(ts)
        #: Check description.
        self.description: str = description
        #: Whether the check is successful or not (boolean).
        self.is_successful: bool = is_successful
        #: Optional check details.
        self.details: str = details


class Attachment(StepLog):
    """
    The log resulting of save/prepare_*attachment* functions.
    Inherits :py:class:`StepLog <lemoncheesecake.reporting.StepLog>`.
    """
    def __init__(self, description: str, filename: str, as_image: bool, ts: float) -> None:
        super().__init__(ts)
        #: Attachment description.
        self.description: str = description
        #: Attachment filename, this is a path relative to the report directory.
        self.filename: str = filename
        #: Whether or not the attachment should be interpreted as an image (boolean).
        self.as_image: bool = as_image


class Url(StepLog):
    """
    The log resulting of log_url function.
    Inherits :py:class:`StepLog <lemoncheesecake.reporting.StepLog>`.
    """
    def __init__(self, description: str, url: str, ts: float) -> None:
        super().__init__(ts)
        #: Optional description.
        self.description: str = description
        #: Actual url.
        self.url: str = url


class Step:
    """
    This class holds logs occurring within a step.
    """
    def __init__(self, description: str) -> None:
        #: Step description.
        self.description: str = description
        #: Parent result.
        self.parent_result: Optional[Result] = None
        self._logs: List[StepLog] = []
        #: Step start time.
        self.start_time: Optional[float] = None
        #: Step end time.
        self.end_time: Optional[float] = None

    def add_log(self, log: StepLog) -> None:
        """
        Add a log to the step.
        """
        log.parent_step = self
        self._logs.append(log)

    def get_logs(self) -> List[StepLog]:
        """
        Get step logs.
        """
        return self._logs

    @staticmethod
    def _is_log_successful(log):
        if isinstance(log, Check):
            return log.is_successful
        elif isinstance(log, Log):
            return log.level != Log.LEVEL_ERROR
        return True

    def is_successful(self) -> bool:
        """
        Return whether or not (as a boolean) the step is successful.
        """
        return all(map(Step._is_log_successful, self._logs))

    @property
    def duration(self) -> Optional[float]:
        """
        Return the duration as a float or None if the step is not yet complete.
        """
        return _get_duration(self.start_time, self.end_time)


class Result:
    """
    Holds the result of setup/teardown phase and it's also the base class of
    :py:class:`TestResult <lemoncheesecake.reporting.TestResult>`.
    """

    #: possible status values for a Result instance
    STATUSES = "passed", "failed", "skipped", "disabled"

    def __init__(self) -> None:
        # please note that this attribute is also defined in TestResult through BaseTest,
        # one will override the other
        #: Parent suite.
        self.parent_suite: Optional[SuiteResult] = None
        #: Result type (it is one of the following: "test_session_setup", "test_session_teardown",
        #: "suite_setup", "suite_teardown", "test").
        self.type: Optional[str] = None
        self._steps: List[Step] = []
        #: Result start time.
        self.start_time: Optional[float] = None
        #: Result end time.
        self.end_time: Optional[float] = None
        #: Result status (one of Result.STATUSES or None if the result is not yet complete).
        self.status: Optional[str] = None
        #: Result status details, if any.
        self.status_details: Optional[str] = None

    def add_step(self, step: Step) -> None:
        """
        Add step to the result.
        """
        step.parent_result = self
        self._steps.append(step)

    def get_steps(self) -> List[Step]:
        """
        Get steps.
        """
        return self._steps

    def is_successful(self) -> bool:
        """
        Return whether or not the result is successful (even if the result is not yet complete).
        """
        if self.status:  # test is finished
            return self.status in ("passed", "disabled")
        else:  # check if the test is successful "so far"
            return all(step.is_successful() for step in self._steps)

    @property
    def duration(self) -> Optional[float]:
        """
        Return the duration as a float or None if the result is not yet complete.
        """
        return _get_duration(self.start_time, self.end_time)


class TestResult(BaseTest, Result):
    """
    Holds the result of a test. Inherits :py:class:`Result <lemoncheesecake.reporting.Result>`.

    :var str ~.name: test name
    :var str ~.description: test description
    :var list ~.tags: test tags
    :var dict ~.properties: test properties, as a dict
    :var dict ~.links: test links, as a list of tuples (`(url, description)` where description can be `None`)
    """
    def __init__(self, name: str, description: str) -> None:
        BaseTest.__init__(self, name, description)
        Result.__init__(self)
        self.type = "test"
        # non-serialized attributes (only set in-memory during test execution):
        self.rank = 0


class SuiteResult(BaseSuite):
    """
    Contains the results of tests and sub-suites within the suite.

    :var str ~.name: test name
    :var str ~.description: test description
    :var list ~.tags: test tags
    :var dict ~.properties: test properties, as a dict
    :var dict ~.links: test links, as a list of tuples (`(url, description)` where description can be `None`)
    """
    def __init__(self, name: str, description: str) -> None:
        BaseSuite.__init__(self, name, description)
        #: The suite start time.
        self.start_time: Optional[float] = None
        #: The suite end time.
        self.end_time: Optional[float] = None
        self._suite_setup: Optional[Result] = None
        self._suite_teardown: Optional[Result] = None
        # non-serialized attributes (only set in-memory during test execution)
        self.rank = 0

    @property
    def suite_setup(self) -> Result:
        """
        The suite setup result (if any).
        """
        return self._suite_setup
    
    @suite_setup.setter
    def suite_setup(self, setup: Result) -> None:
        if setup:
            setup.parent_suite = self
            setup.type = "suite_setup"
        self._suite_setup = setup

    @property
    def suite_teardown(self) -> Result:
        """
        The suite teardown result (if any).
        """
        return self._suite_teardown

    @suite_teardown.setter
    def suite_teardown(self, teardown: Result) -> None:
        if teardown:
            teardown.parent_suite = self
            teardown.type = "suite_teardown"
        self._suite_teardown = teardown

    @property
    def duration(self) -> Optional[float]:
        """
        The suite duration, which is the addition of all results contained in the suite and its sub-suite (recursively).
        """
        return reduce(
            lambda x, y: x + y,
            # result.duration is None if the corresponding result is in progress
            [result.duration or 0 for result in flatten_results([self])],
            0
        )

    def get_tests(self) -> List[TestResult]:
        """
        Return the tests contained in the suite.
        """
        tests = super().get_tests()
        return sorted(tests, key=lambda t: t.rank)

    def get_suites(self) -> List[SuiteResult]:
        """
        Return the sub-suites contained in the suite.
        """
        suites = super().get_suites()
        return sorted(suites, key=lambda s: s.rank)

    def pull_node(self):
        node = BaseSuite.pull_node(self)
        node._suite_setup = None
        node._suite_teardown = None
        return node

    def is_empty(self) -> bool:
        return BaseSuite.is_empty(self) and self._suite_setup is None and self._suite_teardown is None

    def filter(self, result_filter: Callable[[Result], bool]) -> SuiteResult:
        suite = BaseSuite.filter(self, result_filter)
        if self._suite_setup and result_filter(self._suite_setup):
            suite._suite_setup = self._suite_setup
        if self._suite_teardown and result_filter(self._suite_teardown):
            suite._suite_teardown = self._suite_teardown
        return suite


class ReportLocation:
    _TEST_SESSION_SETUP = 0
    _TEST_SESSION_TEARDOWN = 1
    _SUITE_SETUP = 2
    _SUITE_TEARDOWN = 3
    _TEST = 4

    def __init__(self, node_type, node_hierarchy=None):
        self.node_type = node_type
        self.node_hierarchy = node_hierarchy

    @classmethod
    def in_test_session_setup(cls) -> ReportLocation:
        return cls(cls._TEST_SESSION_SETUP)

    @classmethod
    def in_test_session_teardown(cls) -> ReportLocation:
        return cls(cls._TEST_SESSION_TEARDOWN)

    @classmethod
    def in_suite_setup(cls, suite: TreeNodeHierarchy) -> ReportLocation:
        return cls(cls._SUITE_SETUP, normalize_node_hierarchy(suite))

    @classmethod
    def in_suite_teardown(cls, suite: TreeNodeHierarchy) -> ReportLocation:
        return cls(cls._SUITE_TEARDOWN, normalize_node_hierarchy(suite))

    @classmethod
    def in_test(cls, test: TreeNodeHierarchy) -> ReportLocation:
        return cls(cls._TEST, normalize_node_hierarchy(test))

    def get(self, report: Report) -> Union[Result, SuiteResult, TestResult, None]:
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
            ret += "'%s' " % ".".join(self.node_hierarchy)
        ret += ("session setup", "session teardown", "suite setup", "suite teardown", "test")[self.node_type]

        return "<ReportLocation %s>" % ret


def flatten_results(suites: Iterable[SuiteResult]) -> Iterator[Result]:
    for suite in flatten_suites(suites):
        if suite.suite_setup:
            yield suite.suite_setup
        yield from suite.get_tests()
        if suite.suite_teardown:
            yield suite.suite_teardown


class Report:
    DEFAULT_TITLE = "Test Report"

    def __init__(self) -> None:
        self.info = []
        self._test_session_setup: Optional[Result] = None
        self._test_session_teardown: Optional[Result] = None
        self._suites: List[SuiteResult] = []
        #: The test run start time.
        self.start_time: Optional[float] = None
        #: The test run end time.
        self.end_time: Optional[float] = None
        #: The report saving time.
        self.saving_time: Optional[float] = None
        #: The report title.
        self.title = Report.DEFAULT_TITLE
        #: The number of threads used for the test run.
        self.nb_threads = 1
        # both attributes enable the report to be saved back if Report.bind() as been called
        self.backend = None
        self.path = None

    @property
    def test_session_setup(self) -> Optional[Result]:
        """
        The session setup result if any.
        """
        return self._test_session_setup

    @test_session_setup.setter
    def test_session_setup(self, setup: Result) -> None:
        if setup:
            setup.type = "test_session_setup"
        self._test_session_setup = setup

    @property
    def test_session_teardown(self) -> Optional[Result]:
        """
        The session teardown result if any.
        """
        return self._test_session_teardown

    @test_session_teardown.setter
    def test_session_teardown(self, teardown: Result) -> None:
        if teardown:
            teardown.type = "test_session_teardown"
        self._test_session_teardown = teardown

    @property
    def duration(self) -> Optional[float]:
        """
        The test run duration.
        """
        return _get_duration(self.start_time, self.end_time)

    @property
    def nb_tests(self) -> int:
        """
        The number of tests in the report.
        """
        return len(list(self.all_tests()))

    @property
    def parallelized(self) -> bool:
        """
        Whether or not the tests were parallelized.
        """
        return self.nb_threads > 1 and self.nb_tests > 1

    def add_info(self, name: str, value: str) -> None:
        """
        Add extra information (name, value) in the report.
        """
        self.info.append([name, value])
    
    def add_suite(self, suite: SuiteResult) -> None:
        """
        Add suite result to the report.
        """
        self._suites.append(suite)
    
    def get_suites(self) -> List[SuiteResult]:
        """
        Get suite results.
        """
        return sorted(self._suites, key=lambda s: s.rank)

    def get_suite(self, hierarchy: List[str]) -> SuiteResult:
        return find_suite(self._suites, hierarchy)

    def get_test(self, hierarchy: List[str]) -> TestResult:
        return find_test(self._suites, hierarchy)

    def get(self, location: ReportLocation) -> Union[Result, SuiteResult, TestResult, None]:
        return location.get(self)

    def is_successful(self) -> bool:
        """
        Return whether or not the test run is considered as successful.

        Please note that every result is taken into account, including tests but also setups and teardowns.
        """
        return all(result.status in ("passed", "disabled") for result in self.all_results())

    def all_suites(self) -> Iterator[SuiteResult]:
        """
        An iterator over all suite results contained in the report (recursive).
        """
        return flatten_suites(self._suites)

    def all_tests(self) -> Iterator[TestResult]:
        """
        An iterator over all test results contained in the report.
        """
        return flatten_tests(self._suites)

    def all_results(self) -> Iterator[Result]:
        """
        An iterator over all results (tests, setups, teardowns) contained in the report.
        """
        if self.test_session_setup:
            yield self.test_session_setup
        yield from flatten_results(self.get_suites())
        if self.test_session_teardown:
            yield self.test_session_teardown

    def all_steps(self) -> Iterator[Step]:
        """
        An iterator over all steps contained in the report.
        """
        for result in self.all_results():
            yield from result.get_steps()

    def build_message(self, template: str) -> str:
        """
        Build a message from a template that contains variable placeholders.

        Example: with template "Test results: {passed}/{enabled} passed ({passed_pct})" the method will return
        for instance "Test results: 1/2 passed (50%)".

        The following variables are available:

        - ``start_time``: the test run start time

        - ``end_time``: the test run end time

        - ``duration``: the test run duration

        - ``total``: the total number of tests (including disabled tests)

        - ``enabled``: the total number of tests (excluding disabled tests)

        - ``passed``: the number of passed tests

        - ``passed_pct``: the number of passed tests in percentage of enabled tests

        - ``failed``: the number of failed tests

        - ``failed_pct``: the number of failed tests in percentage of enabled tests

        - ``skipped``: the number of skipped tests

        - ``skipped_pct``: the number of skipped tests in percentage of enabled tests

        - ``disabled``: the number of disabled tests

        - ``disabled_pct``: the number of disabled tests in percentage of all tests
        """
        stats = ReportStats.from_report(self)
        variables = {
            name: func(self, stats) for name, func in _report_message_variables.items()
        }
        return template.format(**variables)

    def bind(self, backend: ReportSerializerMixin, path: str) -> None:
        self.backend = backend
        self.path = path

    def save(self):
        """
        Save the report.
        """
        assert self.backend and self.path, "Cannot save unbound report"
        self.backend.save_report(self.path, self)


class ReportStats:
    def __init__(self):
        self.tests_nb = 0
        self.tests_nb_by_status = {s: 0 for s in Result.STATUSES}
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
    def from_results(cls, results: List[Result], duration: Optional[int]) -> ReportStats:
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
    def from_report(cls, report: Report) -> ReportStats:
        return cls.from_results(list(report.all_results()), report.duration)

    @classmethod
    def from_suites(cls, suites: List[SuiteResult], parallelized: bool) -> ReportStats:
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
