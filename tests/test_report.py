import time

from lemoncheesecake.reporting.report import format_time_as_iso8601, parse_iso8601_time, Step, \
    TestResult as TstResult  # we change the name of TestResult so that pytest won't try to interpret as a test class

from helpers.report import assert_report_stats, make_check, make_step, make_test_result, make_result, \
    make_suite_result, make_log, make_report

NOW = time.time()


def _test_timestamp_round(raw, rounded):
    assert parse_iso8601_time(format_time_as_iso8601(raw)) == rounded


def test_format_and_parse_iso8601_time_1():
    _test_timestamp_round(1485093460.874194, 1485093460.874)


def test_format_and_parse_iso8601_time_2():
    _test_timestamp_round(1485093460.874794, 1485093460.875)


def test_format_and_parse_iso8601_time_3():
    _test_timestamp_round(1485093460.999001, 1485093460.999)


def test_format_and_parse_iso8601_time_4():
    _test_timestamp_round(1485093460.999999, 1485093461.0)


def test_format_and_parse_iso8601_time_5():
    _test_timestamp_round(1485105524.353112, 1485105524.353)


def test_report_stats_simple():
    report = make_report(suites=[
        make_suite_result(tests=[
            make_test_result(steps=[make_step(entries=[make_check(True)])])
        ])
    ])

    assert_report_stats(report, expected_passed_tests=1)


def test_report_stats_failure():
    report = make_report(suites=[
        make_suite_result(tests=[
            make_test_result(steps=[make_step(entries=[make_check(True), make_log("error")])])
        ])
    ])

    assert_report_stats(report, expected_failed_tests=1)


def test_report_stats_skipped():
    report = make_report(suites=[
        make_suite_result(tests=[
            make_test_result(status="skipped")
        ])
    ])

    assert_report_stats(report, expected_skipped_tests=1)


def test_test_duration_unfinished():
    test = TstResult("test", "test")
    test.start_time = NOW
    assert test.duration is None


def test_test_duration_finished():
    test = TstResult("test", "test")
    test.start_time = NOW
    test.end_time = NOW + 1.0
    assert test.duration == 1.0


def test_step_duration_unfinished():
    step = Step("step")
    step.start_time = NOW
    assert step.duration is None


def test_step_duration_finished():
    step = Step("step")
    step.start_time = NOW
    step.end_time = NOW + 1.0
    assert step.duration == 1.0


def test_suite_duration():
    suite = make_suite_result(tests=[
        make_test_result(start_time=NOW, end_time=NOW+1),
        make_test_result(start_time=NOW+1, end_time=NOW+2)
    ])

    assert suite.duration == 2


def test_suite_duration_with_setup():
    suite = make_suite_result(
        setup=make_result(start_time=NOW, end_time=NOW+1),
        tests=[make_test_result(start_time=NOW+1, end_time=NOW+2)],
    )

    assert suite.duration == 2


def test_suite_duration_with_teardown():
    suite = make_suite_result(
        tests=[make_test_result(start_time=NOW+1, end_time=NOW+2)],
        teardown=make_result(start_time=NOW+2, end_time=NOW+3)
    )

    assert suite.duration == 2

# TODO: report_stats lake tests
