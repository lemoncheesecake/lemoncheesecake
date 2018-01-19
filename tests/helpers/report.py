'''
Created on Sep 30, 2016

@author: nicolas
'''


from lemoncheesecake.suite import load_suite_from_class
from lemoncheesecake import reporting


def assert_check_data(actual, expected):
    assert actual.description == expected.description
    assert actual.outcome == expected.outcome
    assert actual.details == expected.details


def assert_log_data(actual, expected):
    assert actual.level == expected.level
    assert actual.message == expected.message
    assert round(actual.time, 3) == round(expected.time, 3)


def assert_attachment_data(actual, expected):
    assert actual.description == expected.description
    assert actual.filename == expected.filename


def assert_url_data(actual, expected):
    assert actual.description == expected.description
    assert actual.url == expected.url


def assert_step_data(actual, expected):
    assert round(actual.start_time, 3) == round(expected.start_time, 3)
    assert round(actual.end_time, 3) == round(expected.end_time, 3)
    assert actual.description == expected.description
    assert len(actual.entries) == len(expected.entries)
    for actual_entry, expected_entry in zip(actual.entries, expected.entries):
        assert actual_entry.__class__ == expected_entry.__class__
        if isinstance(actual_entry, reporting.LogData):
            assert_log_data(actual_entry, expected_entry)
        elif isinstance(actual_entry, reporting.CheckData):
            assert_check_data(actual_entry, expected_entry)
        elif isinstance(actual_entry, reporting.AttachmentData):
            assert_attachment_data(actual_entry, expected_entry)
        elif isinstance(actual_entry, reporting.UrlData):
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
    assert round(actual.start_time, 3) == round(expected.start_time, 3)
    assert round(actual.end_time, 3) == round(expected.end_time, 3)

    assert len(actual.steps) == len(expected.steps)
    for actual_step, expected_step in zip(actual.steps, expected.steps):
        assert_step_data(actual_step, expected_step)


def assert_hook_data(actual, expected):
    if expected == None:
        assert actual == None
    else:
        assert actual.outcome == expected.outcome
        assert round(actual.start_time, 3) == round(expected.start_time, 3)
        assert round(actual.end_time, 3) == round(expected.end_time, 3)
        assert len(actual.steps) == len(expected.steps)
        for actual_step, expected_step in zip(actual.steps, expected.steps):
            assert_step_data(actual_step, expected_step)


def assert_suite_data(actual, expected):
    assert actual.name == expected.name
    assert actual.description == expected.description
    if expected.parent_suite == None:
        assert actual.parent_suite == None
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


def assert_report(actual, expected):
    assert actual.title == expected.title
    assert actual.info == expected.info
    assert round(actual.start_time, 3) == round(expected.start_time, 3)
    assert round(actual.end_time, 3) == round(expected.end_time, 3)
    assert round(actual.report_generation_time, 3) == round(expected.report_generation_time, 3)
    assert len(actual.suites) == len(expected.suites)

    assert_hook_data(actual.test_session_setup, expected.test_session_setup)

    for actual_suite, expected_suite in zip(actual.suites, expected.suites):
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

    assert_steps_data(test_data.steps)


def assert_suite_data_from_suite(suite_data, suite):
    assert suite_data.name == suite.name
    assert suite_data.description == suite.description
    assert suite_data.tags == suite.tags
    assert suite_data.properties == suite.properties
    assert suite_data.links == suite.links

    if suite.has_hook("setup_suite"):
        assert suite_data.suite_setup != None
        assert suite_data.suite_setup.start_time != None
        assert suite_data.suite_setup.end_time != None
        assert_steps_data(suite_data.suite_setup.steps)

    assert len(suite_data.get_tests()) == len(suite.get_tests())
    for test_data, test in zip(suite_data.get_tests(), suite.get_tests()):
        assert_test_data_from_test(test_data, test)

    assert len(suite_data.get_suites()) == len(suite.get_suites())
    for sub_suite_data, sub_suite in zip(suite_data.get_suites(), suite.get_suites()):
        assert_suite_data_from_suite(sub_suite_data, sub_suite)

    if suite.has_hook("teardown_suite"):
        assert suite_data.suite_teardown != None
        assert suite_data.suite_teardown.start_time != None
        assert suite_data.suite_teardown.end_time != None
        assert_steps_data(suite_data.suite_teardown.steps)


def assert_report_from_suites(report, suite_classes):
    assert report.start_time != None
    assert report.end_time != None
    assert report.report_generation_time != None
    assert len(report.suites) == len(suite_classes)
    for suite_data, suite_class in zip(report.suites, suite_classes):
        suite = load_suite_from_class(suite_class)
        assert_suite_data_from_suite(suite_data, suite)


def assert_report_from_suite(report, suite_class):
    assert_report_from_suites(report, [suite_class])


def assert_report_stats(report,
                        expected_test_successes=0, expected_test_failures=0, expected_test_skippeds=0,
                        expected_errors=0,
                        expected_check_successes=0, expected_check_failures=0,
                        expected_error_logs=0, expected_warning_logs=0):
    stats = report.get_stats()
    assert stats.tests == expected_test_successes + expected_test_failures + expected_test_skippeds
    assert stats.test_statuses["passed"] == expected_test_successes
    assert stats.test_statuses["failed"] == expected_test_failures
    assert stats.test_statuses["skipped"] == expected_test_skippeds
    assert stats.errors == expected_errors
    assert stats.checks == expected_check_successes + expected_check_failures
    assert stats.check_successes == expected_check_successes
    assert stats.check_failures == expected_check_failures
    assert stats.error_logs == expected_error_logs
    assert stats.warning_logs == expected_warning_logs
