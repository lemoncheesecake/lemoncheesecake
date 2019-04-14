from __future__ import print_function

from typing import Iterable

from lemoncheesecake.testtree import TreeLocation
from lemoncheesecake.reporting import Report, StepData, TestData, SuiteData, LogData, AttachmentData, UrlData, CheckData
from lemoncheesecake import events
from lemoncheesecake.exceptions import LemonCheesecakeInternalError


class EventReplayer(object):
    def __init__(self, eventmgr):
        self.eventmgr = eventmgr

    def replay_step(self, location, step):
        # type: (TreeLocation, StepData) -> None
        self.eventmgr.fire(events.StepEvent(location, step.description, event_time=step.start_time))
        for entry in step.entries:
            if isinstance(entry, LogData):
                self.eventmgr.fire(
                    events.LogEvent(
                        location, step.description, entry.level, entry.message, entry.time
                    )
                )
            elif isinstance(entry, AttachmentData):
                self.eventmgr.fire(
                    events.LogAttachmentEvent(
                        location, step.description, entry.filename, entry.description, entry.as_image, entry.time
                    )
                )
            elif isinstance(entry, UrlData):
                self.eventmgr.fire(
                    events.LogUrlEvent(
                        location, step.description, entry.url, entry.description, entry.time
                    )
                )
            elif isinstance(entry, CheckData):
                self.eventmgr.fire(
                    events.CheckEvent(
                        location, step.description, entry.description, entry.outcome, entry.details, entry.time
                    )
                )
            else:
                raise LemonCheesecakeInternalError("Unknown step entry %s" % entry)

    def replay_steps(self, location, steps):
        # type: (TreeLocation, Iterable[StepData]) -> None
        for step in steps:
            self.replay_step(location, step)

    def replay_test(self, test):
        # type: (TestData) -> None
        if test.status in ("passed", "failed", None):  # None means "in progress"
            self.eventmgr.fire(events.TestStartEvent(test, test.start_time))
            self.replay_steps(TreeLocation.in_test(test), test.steps)
            if test.end_time:
                self.eventmgr.fire(events.TestEndEvent(test, test.end_time))
        elif test.status == "skipped":
            self.eventmgr.fire(events.TestSkippedEvent(test, test.status_details, test.start_time))
        elif test.status == "disabled":
            self.eventmgr.fire(events.TestDisabledEvent(test, test.status_details, test.start_time))
        else:
            raise LemonCheesecakeInternalError("Unknown test status '%s'" % test.status)

    def replay_suite(self, suite):
        # type: (SuiteData) -> None

        self.eventmgr.fire(events.SuiteStartEvent(suite, suite.start_time))

        if suite.suite_setup:
            self.eventmgr.fire(events.SuiteSetupStartEvent(suite, suite.suite_setup.start_time))
            self.replay_steps(TreeLocation.in_suite_setup(suite), suite.suite_setup.steps)
            if suite.suite_setup.end_time:
                self.eventmgr.fire(events.SuiteSetupEndEvent(suite, suite.suite_setup.end_time))

        for test in suite.get_tests():
            self.replay_test(test)

        for sub_suite in suite.get_suites():
            self.replay_suite(sub_suite)

        if suite.suite_teardown:
            self.eventmgr.fire(events.SuiteTeardownStartEvent(suite, suite.suite_teardown.start_time))
            self.replay_steps(TreeLocation.in_suite_teardown(suite), suite.suite_teardown.steps)
            if suite.suite_teardown.end_time:
                self.eventmgr.fire(events.SuiteTeardownEndEvent(suite, suite.suite_teardown.end_time))

        if suite.end_time:
            self.eventmgr.fire(events.SuiteEndEvent(suite, suite.end_time))

    def replay_report(self, report):
        # type: (Report) -> None

        self.eventmgr.fire(events.TestSessionStartEvent(report, report.start_time))

        if report.test_session_setup:
            self.eventmgr.fire(events.TestSessionSetupStartEvent(report.test_session_setup.start_time))
            self.replay_steps(TreeLocation.in_test_session_setup(), report.test_session_setup.steps)
            if report.test_session_setup.end_time:
                self.eventmgr.fire(events.TestSessionSetupEndEvent(report.test_session_setup.end_time))

        for suite in report.get_suites():
            self.replay_suite(suite)

        if report.test_session_teardown:
            self.eventmgr.fire(events.TestSessionTeardownStartEvent(report.test_session_teardown.start_time))
            self.replay_steps(TreeLocation.in_test_session_teardown(), report.test_session_teardown.steps)
            if report.test_session_teardown.end_time:
                self.eventmgr.fire(events.TestSessionTeardownEndEvent(report.test_session_teardown.end_time))

        if report.end_time:
            self.eventmgr.fire(events.TestSessionEndEvent(report, report.end_time))


def replay_report_events(report, eventmgr):
    replayer = EventReplayer(eventmgr)
    replayer.replay_report(report)
