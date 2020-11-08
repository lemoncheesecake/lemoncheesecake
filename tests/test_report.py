import time

import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.reporting.report import format_time_as_iso8601, parse_iso8601_time, Step, \
    check_report_message_template, \
    TestResult as TstResult  # we change the name of TestResult so that pytest won't try to interpret as a test class

from helpers.report import assert_report_stats, make_check, make_step, make_test_result, make_result, \
    make_suite_result, make_log, make_report
from helpers.runner import run_suite_class

NOW = time.time()
CURRENT_YEAR = time.localtime().tm_year


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
            make_test_result(steps=[make_step(logs=[make_check(True)])])
        ])
    ])

    assert_report_stats(report, expected_passed_tests=1)


def test_report_stats_failure():
    report = make_report(suites=[
        make_suite_result(tests=[
            make_test_result(steps=[make_step(logs=[make_check(True), make_log("error")])])
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


def test_is_successful_is_true():
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.log_info("some log")

    report = run_suite_class(suite)
    assert report.is_successful()


def test_is_successful():
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.log_error("some error")

    report = run_suite_class(suite)
    assert not report.is_successful()


def test_is_successful_with_disabled_test():
    @lcc.suite("suite")
    class suite:
        @lcc.test("test_1")
        def test_1(self):
            lcc.log_info("some log")

        @lcc.test("test_2")
        @lcc.disabled()
        def test_2(self):
            lcc.log_info("some log")

    report = run_suite_class(suite)
    assert report.is_successful()


def test_is_successful_with_failed_test():
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.log_error("some error")

    report = run_suite_class(suite)
    assert not report.is_successful()


def test_is_successful_with_failed_teardown():
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.log_info("some log")

        def teardown_suite(self):
            lcc.log_error("some error")

    report = run_suite_class(suite)
    assert not report.is_successful()


def test_check_report_message_template_ok():
    template = "{passed} test passed"
    assert check_report_message_template(template) == template


def test_check_report_message_template_ko():
    with pytest.raises(ValueError):
        assert check_report_message_template("{invalid_var}'")


@pytest.fixture()
def report_sample():
    @lcc.suite()
    class suite:
        @lcc.test()
        def test_1(self):
            pass

        @lcc.test()
        @lcc.disabled()
        def test_2(self):
            pass

        @lcc.test()
        def test_3(self):
            lcc.log_error("some issue")

        @lcc.test()
        def test_4(self):
            lcc.log_info("everything ok")

    return run_suite_class(suite)


def test_report_build_message_with_start_time(report_sample):
    assert str(CURRENT_YEAR) in report_sample.build_message("{start_time}")


def test_report_build_message_with_end_time(report_sample):
    assert str(CURRENT_YEAR) in report_sample.build_message("{end_time}")


def test_report_build_message_with_duration(report_sample):
    report_sample.end_time = report_sample.start_time + 1

    assert report_sample.build_message("{duration}") == "1s"


def test_report_build_message_with_total(report_sample):
    assert report_sample.build_message("{total}") == "4"


def test_report_build_message_with_enabled(report_sample):
    assert report_sample.build_message("{enabled}") == "3"


def test_report_build_message_with_passed(report_sample):
    assert report_sample.build_message("{passed}") == "2"


def test_report_build_message_with_passed_pct(report_sample):
    assert report_sample.build_message("{passed_pct}") == "66%"


def test_report_build_message_with_failed(report_sample):
    assert report_sample.build_message("{failed}") == "1"


def test_report_build_message_with_failed_pct(report_sample):
    assert report_sample.build_message("{failed_pct}") == "33%"


def test_report_build_message_with_skipped():
    report = make_report([
        make_suite_result(tests=[
            make_test_result(status="passed"), make_test_result(status="passed"), make_test_result(status="skipped")
        ])
    ])
    assert report.build_message("{skipped}") == "1"


def test_report_build_message_with_skipped_pct():
    report = make_report([
        make_suite_result(tests=[
            make_test_result(status="passed"), make_test_result(status="passed"), make_test_result(status="skipped")
        ])
    ])
    assert report.build_message("{skipped_pct}") == "33%"


def test_report_build_message_with_disabled(report_sample):
    assert report_sample.build_message("{disabled}") == "1"


def test_report_build_message_with_disabled_pct(report_sample):
    assert report_sample.build_message("{disabled_pct}") == "25%"


# TODO: report_stats lake tests
