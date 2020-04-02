'''
Created on Sep 30, 2016

@author: nicolas
'''


import os.path
import time

import pytest

from lemoncheesecake.suite import load_suite_from_class
from lemoncheesecake import reporting
from lemoncheesecake.session import get_session
from lemoncheesecake.reporting import Report, ReportStats, Result, SuiteResult, TestResult, Step, Log, Check, JsonBackend,\
    flatten_results


###
# Helpers that make easier to build a custom report for tests
###


def make_log(level, message=None, ts=None):
    return Log(level, message if message else "some %s" % level, ts or time.time())


def make_check(is_successful, description="some check", details=None, ts=None):
    return Check(description, is_successful, details, ts or time.time())


def make_step(description="Step", entries=(), start_time=NotImplemented, end_time=NotImplemented):
    step = Step(description)
    step.entries.extend(entries)

    if start_time is not NotImplemented:
        step.start_time = start_time
    elif entries:
        step.start_time = entries[0].time
    else:
        step.start_time = time.time()

    if end_time is not NotImplemented:
        step.end_time = end_time
    elif entries:
        step.end_time = entries[-1].time
    else:
        step.end_time = time.time()

    return step


def _set_result(result, steps=(), status=NotImplemented, start_time=NotImplemented, end_time=NotImplemented):
    for step in steps:
        result.add_step(step)

    if start_time is not NotImplemented:
        result.start_time = start_time
    elif steps:
        result.start_time = steps[0].start_time
    else:
        result.start_time = time.time()

    if end_time is not NotImplemented:
        result.end_time = end_time
    elif steps:
        result.end_time = steps[-1].end_time
    else:
        result.end_time = time.time()

    if status is not NotImplemented:
        result.status = status
    else:
        result.status = "passed" if result.is_successful() else "failed"


def make_result(steps=(), status=NotImplemented, start_time=NotImplemented, end_time=NotImplemented):
    result = Result()
    _set_result(result, steps, status, start_time, end_time)
    return result


_counter = 0  # used to create some unicity in test/suite names/descriptions


def make_test_result(name=None, description=None, steps=(), status=NotImplemented, start_time=NotImplemented, end_time=NotImplemented):
    global _counter

    test = TestResult(name or "test_%d" % _counter, description or "Test %d" % _counter)
    _counter += 1

    _set_result(test, steps, status, start_time, end_time)

    return test


def make_suite_result(name=None, description=None, tests=(), sub_suites=(), setup=None, teardown=None,
                      start_time=NotImplemented, end_time=NotImplemented):
    global _counter

    suite = SuiteResult(name or "suite_%d" % _counter, description or "Suite %d" % _counter)
    _counter += 1

    if setup:
        suite.suite_setup = setup

    if teardown:
        suite.suite_teardown = teardown

    for test in tests:
        suite.add_test(test)

    for sub_suite in sub_suites:
        suite.add_suite(sub_suite)

    results = list(flatten_results([suite]))

    if start_time is not NotImplemented:
        suite.start_time = start_time
    elif results:
        suite.start_time = results[0].start_time
    else:
        suite.start_time = time.time()

    if end_time is not NotImplemented:
        suite.end_time = end_time
    elif results:
        suite.end_time = results[-1].end_time
    else:
        suite.end_time = time.time()

    return suite


def make_report(suites=(), setup=None, teardown=None):
    report = Report()

    if setup:
        report.test_session_setup = setup
    for suite in suites:
        report.add_suite(suite)
    if teardown:
        report.test_session_teardown = teardown

    results = list(report.all_results())
    if results:
        report.start_time = results[0].start_time
        report.end_time = results[-1].end_time
        report.report_generation_time = time.time()
    else:
        report.start_time = report.end_time = report.report_generation_time = time.time()

    return report


###
# Some helpful fixtures
###


def make_report_in_progress():
    # create a pseudo report where all elements that can be "in-progress" (meaning without
    # an end time) are present in the report
    now = time.time()
    return make_report(
        setup=make_result(start_time=now, end_time=None),
        teardown=make_result(start_time=now, end_time=None),
        suites=[make_suite_result(
            "suite", "suite",
            start_time=now, end_time=None,
            setup=make_result(start_time=now, end_time=None),
            teardown=make_result(start_time=now, end_time=None),
            tests=[
                make_test_result(
                    "test_1", "test_1", start_time=now, end_time=None, status=None,
                    steps=[make_step("step", start_time=now, end_time=None, entries=[make_log("info", "message", ts=now)])]
                ),
                make_test_result(
                    "test_2", "test_2", start_time=now, end_time=now+1, status="passed",
                    steps=[make_step("step", start_time=now, end_time=now+1, entries=[make_log("info", "message", ts=now)])]
                )
            ]
        )]
    )


@pytest.fixture()
def report_in_progress():
    return make_report_in_progress()


@pytest.fixture()
def report_in_progress_path(tmpdir):
    backend = JsonBackend()
    report_path = os.path.join(tmpdir.strpath, "report.json")
    backend.save_report(report_path, make_report_in_progress())
    return report_path


###
# Assertions helpers for quick report checks
###

def _assert_tests_status(report, status, expected):
    actual = [t.path for t in report.all_tests() if t.status == status]
    assert sorted(actual) == sorted(expected)


def assert_test_statuses(report, passed=(), failed=(), skipped=(), disabled=()):
    _assert_tests_status(report, "passed", passed)
    _assert_tests_status(report, "failed", failed)
    _assert_tests_status(report, "skipped", skipped)
    _assert_tests_status(report, "disabled", disabled)


def assert_report_node_success(report, location, expected):
    node = report.get(location)
    assert node.is_successful() == expected


def _assert_test_status(report, status):
    test = get_last_test(report)
    _assert_tests_status(report, status, [test.path])


def assert_test_passed(report):
    _assert_test_status(report, "passed")


def assert_test_failed(report):
    _assert_test_status(report, "failed")


def assert_test_skipped(report):
    _assert_test_status(report, "skipped")


def get_last_suite(report):
    return next(reversed(list(report.all_suites())))


def get_last_test(report):
    return next(reversed(list(report.all_tests())))


def assert_last_test_status(report, status):
    test = get_last_test(report)
    assert test.status == status


def get_last_log(report):
    test = get_last_test(report)
    return next(entry for entry in reversed(test.get_steps()[-1].entries) if isinstance(entry, reporting.Log))


def get_last_logged_check(report):
    test = get_last_test(report)
    return next(entry for entry in reversed(test.get_steps()[-1].entries) if isinstance(entry, reporting.Check))


def get_last_attachment(report):
    test = get_last_test(report)
    return next(entry for entry in reversed(test.get_steps()[-1].entries) if isinstance(entry, reporting.Attachment))


def assert_time(actual, expected):
    assert round(actual, 3) == round(expected, 3)


def assert_attachment(attachment, filename, description, as_image, content, file_reader):
    assert attachment.filename.endswith(filename)
    assert attachment.description == description
    assert attachment.as_image is as_image
    assert file_reader(os.path.join(get_session().report_dir, attachment.filename)) == content


def get_last_test_checks(report):
    test = get_last_test(report)
    checks = []
    for step in test.get_steps():
        for entry in step.entries:
            if isinstance(entry, reporting.Check):
                checks.append(entry)
    return checks


def count_logs(report, log_level):
    count = 0
    for test in report.all_tests():
        for step in test.get_steps():
            for entry in step.entries:
                if isinstance(entry, reporting.Log) and entry.level == log_level:
                    count += 1
    return count


def assert_test_checks(test, expected_successes=0, expected_failures=0):
    successes = 0
    failures = 0

    for step in test.get_steps():
        for entry in step.entries:
            if isinstance(entry, reporting.Check):
                if entry.is_successful:
                    successes += 1
                else:
                    failures += 1

    assert successes == expected_successes
    assert failures == expected_failures


###
# Assertions for the whole report content
###

def assert_check_data(actual, expected):
    assert actual.description == expected.description
    assert actual.is_successful == expected.is_successful
    assert actual.details == expected.details
    assert_time(actual.time, expected.time)


def assert_log_data(actual, expected):
    assert actual.level == expected.level
    assert actual.message == expected.message
    assert_time(actual.time, expected.time)


def assert_attachment_data(actual, expected):
    assert actual.description == expected.description
    assert actual.filename == expected.filename
    assert actual.as_image == expected.as_image
    assert_time(actual.time, expected.time)


def assert_url_data(actual, expected):
    assert actual.description == expected.description
    assert actual.url == expected.url
    assert_time(actual.time, expected.time)


def assert_step_data(actual, expected):
    assert_time(actual.start_time, expected.start_time)
    if expected.end_time is None:
        assert actual.end_time is None
    else:
        assert_time(actual.end_time, expected.end_time)
    assert actual.description == expected.description
    assert len(actual.entries) == len(expected.entries)
    for actual_entry, expected_entry in zip(actual.entries, expected.entries):
        assert actual_entry.__class__ == expected_entry.__class__
        if isinstance(actual_entry, reporting.Log):
            assert_log_data(actual_entry, expected_entry)
        elif isinstance(actual_entry, reporting.Check):
            assert_check_data(actual_entry, expected_entry)
        elif isinstance(actual_entry, reporting.Attachment):
            assert_attachment_data(actual_entry, expected_entry)
        elif isinstance(actual_entry, reporting.Url):
            assert_url_data(actual_entry, expected_entry)
        else:
            raise Exception("Unknown class '%s'" % actual.__class__.__name__)


def assert_test_data(actual, expected):
    assert actual.name == expected.name
    assert actual.description == expected.description
    assert actual.tags == expected.tags
    assert actual.properties == expected.properties
    assert actual.links == expected.links
    assert actual.status == expected.status
    assert actual.status_details == expected.status_details
    assert_time(actual.start_time, expected.start_time)
    if expected.end_time is None:
        assert actual.end_time is None
    else:
        assert_time(actual.end_time, expected.end_time)
    assert len(actual.get_steps()) == len(expected.get_steps())
    for actual_step, expected_step in zip(actual.get_steps(), expected.get_steps()):
        assert_step_data(actual_step, expected_step)


def assert_hook_data(actual, expected):
    if expected is None:
        assert actual is None
    else:
        assert actual.status == expected.status
        assert_time(actual.start_time, expected.start_time)
        if expected.end_time is None:
            assert actual.end_time is None
        else:
            assert_time(actual.end_time, expected.end_time)
        assert len(actual.get_steps()) == len(expected.get_steps())
        for actual_step, expected_step in zip(actual.get_steps(), expected.get_steps()):
            assert_step_data(actual_step, expected_step)


def assert_suite_data(actual, expected):
    assert actual.name == expected.name
    assert actual.description == expected.description
    assert_time(actual.start_time, expected.start_time)
    if expected.end_time is None:
        assert actual.end_time is None
    else:
        assert_time(actual.end_time, expected.end_time)
    if expected.parent_suite is None:
        assert actual.parent_suite is None
    else:
        assert actual.parent_suite.name == expected.parent_suite.name
    assert actual.tags == expected.tags
    assert actual.properties == expected.properties
    assert actual.links == expected.links

    assert_hook_data(actual.suite_setup, expected.suite_setup)

    assert len(actual.get_tests()) == len(expected.get_tests())
    for actual_test, expected_test in zip(actual.get_tests(), expected.get_tests()):
        assert_test_data(actual_test, expected_test)

    assert len(actual.get_suites()) == len(expected.get_suites())
    for actual_subsuite, expected_subsuite in zip(actual.get_suites(), expected.get_suites()):
        assert_suite_data(actual_subsuite, expected_subsuite)

    assert_hook_data(actual.suite_teardown, expected.suite_teardown)


def assert_report(actual, expected, is_persisted=True):
    assert actual.title == expected.title
    assert actual.info == expected.info
    assert_time(actual.start_time, expected.start_time)
    if expected.end_time is None:
        assert actual.end_time is None
    else:
        assert_time(actual.end_time, expected.end_time)
    if is_persisted:
        assert actual.report_generation_time is not None
    else:
        assert actual.report_generation_time is None
    assert actual.nb_threads == expected.nb_threads
    assert len(actual.get_suites()) == len(expected.get_suites())

    assert_hook_data(actual.test_session_setup, expected.test_session_setup)

    for actual_suite, expected_suite in zip(actual.get_suites(), expected.get_suites()):
        assert_suite_data(actual_suite, expected_suite)

    assert_hook_data(actual.test_session_teardown, expected.test_session_teardown)


def assert_steps_data(steps):
    for step in steps:
        assert step.start_time
        assert step.end_time >= step.start_time


def assert_test_data_from_test(test_data, test):
    assert test_data.name == test.name
    assert test_data.description == test.description
    assert test_data.tags == test.tags
    assert test_data.properties == test.properties
    assert test_data.links == test.links

    assert_steps_data(test_data.get_steps())


def assert_suite_data_from_suite(suite_data, suite):
    assert suite_data.name == suite.name
    assert suite_data.description == suite.description
    assert suite_data.tags == suite.tags
    assert suite_data.properties == suite.properties
    assert suite_data.links == suite.links

    if suite.has_hook("setup_suite"):
        assert suite_data.suite_setup is not None
        assert suite_data.suite_setup.start_time is not None
        assert suite_data.suite_setup.end_time is not None
        assert_steps_data(suite_data.suite_setup.get_steps())

    assert len(suite_data.get_tests()) == len(suite.get_tests())
    for test_data, test in zip(suite_data.get_tests(), suite.get_tests()):
        assert_test_data_from_test(test_data, test)

    assert len(suite_data.get_suites()) == len(suite.get_suites())
    for sub_suite_data, sub_suite in zip(suite_data.get_suites(), suite.get_suites()):
        assert_suite_data_from_suite(sub_suite_data, sub_suite)

    if suite.has_hook("teardown_suite"):
        assert suite_data.suite_teardown is not None
        assert suite_data.suite_teardown.start_time is not None
        assert suite_data.suite_teardown.end_time is not None
        assert_steps_data(suite_data.suite_teardown.get_steps())


def assert_report_from_suites(report, suite_classes):
    assert report.start_time is not None
    assert report.end_time is not None
    assert len(report.get_suites()) == len(suite_classes)
    for suite_data, suite_class in zip(report.get_suites(), suite_classes):
        suite = load_suite_from_class(suite_class)
        assert_suite_data_from_suite(suite_data, suite)


def assert_report_from_suite(report, suite_class):
    assert_report_from_suites(report, [suite_class])


def assert_report_stats(report,
                        expected_passed_tests=0, expected_failed_tests=0, expected_skipped_tests=0):
    stats = ReportStats.from_report(report)
    assert stats.tests_nb == expected_passed_tests + expected_failed_tests + expected_skipped_tests
    assert stats.tests_nb_by_status["passed"] == expected_passed_tests
    assert stats.tests_nb_by_status["failed"] == expected_failed_tests
    assert stats.tests_nb_by_status["skipped"] == expected_skipped_tests
