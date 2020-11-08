from __future__ import print_function

import threading

from typing import Iterable

from lemoncheesecake.reporting import Report, Step, TestResult, SuiteResult, Log, Attachment, Url, Check, ReportLocation
from lemoncheesecake import events
from lemoncheesecake.events import EventManager


def _replay_step(location, step, eventmgr):
    # type: (ReportLocation, Step, EventManager) -> None

    thread_id = threading.current_thread().ident
    eventmgr.fire(events.StepStartEvent(location, step.description, thread_id, event_time=step.start_time))

    for log in step.get_logs():
        if isinstance(log, Log):
            eventmgr.fire(
                events.LogEvent(
                    location, step.description, thread_id, log.level, log.message, log.time
                )
            )
        elif isinstance(log, Attachment):
            eventmgr.fire(
                events.LogAttachmentEvent(
                    location, step.description, thread_id, log.filename, log.description,
                    log.as_image, log.time
                )
            )
        elif isinstance(log, Url):
            eventmgr.fire(
                events.LogUrlEvent(
                    location, step.description, thread_id, log.url, log.description, log.time
                )
            )
        elif isinstance(log, Check):
            eventmgr.fire(
                events.CheckEvent(
                    location, step.description, thread_id, log.description, log.is_successful,
                    log.details, log.time
                )
            )
        else:
            raise ValueError("Unknown step log %s" % log)

    eventmgr.fire(events.StepEndEvent(location, step.description, thread_id, event_time=step.end_time))


def _replay_steps_events(location, steps, eventmgr):
    # type: (ReportLocation, Iterable[Step], EventManager) -> None
    for step in steps:
        _replay_step(location, step, eventmgr)


def _replay_test_events(test, eventmgr):
    # type: (TestResult, EventManager) -> None
    if test.status in ("passed", "failed", None):  # None means "in progress"
        eventmgr.fire(events.TestStartEvent(test, test.start_time))
        _replay_steps_events(ReportLocation.in_test(test), test.get_steps(), eventmgr)
        if test.end_time:
            eventmgr.fire(events.TestEndEvent(test, test.end_time))
    elif test.status == "skipped":
        eventmgr.fire(events.TestSkippedEvent(test, test.status_details, test.start_time))
    elif test.status == "disabled":
        eventmgr.fire(events.TestDisabledEvent(test, test.status_details, test.start_time))
    else:
        raise ValueError("Unknown test status '%s'" % test.status)


def _replay_suite_events(suite, eventmgr):
    # type: (SuiteResult, EventManager) -> None

    eventmgr.fire(events.SuiteStartEvent(suite, suite.start_time))

    if suite.suite_setup:
        eventmgr.fire(events.SuiteSetupStartEvent(suite, suite.suite_setup.start_time))
        _replay_steps_events(ReportLocation.in_suite_setup(suite), suite.suite_setup.get_steps(), eventmgr)
        if suite.suite_setup.end_time:
            eventmgr.fire(events.SuiteSetupEndEvent(suite, suite.suite_setup.end_time))

    for test in suite.get_tests():
        _replay_test_events(test, eventmgr)

    for sub_suite in suite.get_suites():
        _replay_suite_events(sub_suite, eventmgr)

    if suite.suite_teardown:
        eventmgr.fire(events.SuiteTeardownStartEvent(suite, suite.suite_teardown.start_time))
        _replay_steps_events(ReportLocation.in_suite_teardown(suite), suite.suite_teardown.get_steps(), eventmgr)
        if suite.suite_teardown.end_time:
            eventmgr.fire(events.SuiteTeardownEndEvent(suite, suite.suite_teardown.end_time))

    if suite.end_time:
        eventmgr.fire(events.SuiteEndEvent(suite, suite.end_time))


def replay_report_events(report, eventmgr):
    # type: (Report, EventManager) -> None

    eventmgr.fire(events.TestSessionStartEvent(report, report.start_time))

    if report.test_session_setup:
        eventmgr.fire(events.TestSessionSetupStartEvent(report.test_session_setup.start_time))
        _replay_steps_events(ReportLocation.in_test_session_setup(), report.test_session_setup.get_steps(), eventmgr)
        if report.test_session_setup.end_time:
            eventmgr.fire(events.TestSessionSetupEndEvent(report.test_session_setup.end_time))

    for suite in report.get_suites():
        _replay_suite_events(suite, eventmgr)

    if report.test_session_teardown:
        eventmgr.fire(events.TestSessionTeardownStartEvent(report.test_session_teardown.start_time))
        _replay_steps_events(ReportLocation.in_test_session_teardown(), report.test_session_teardown.get_steps(), eventmgr)
        if report.test_session_teardown.end_time:
            eventmgr.fire(events.TestSessionTeardownEndEvent(report.test_session_teardown.end_time))

    if report.end_time:
        eventmgr.fire(events.TestSessionEndEvent(report, report.end_time))
