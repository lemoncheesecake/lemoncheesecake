import time

import pytest
from pytest_mock import mocker


import lemoncheesecake.api as lcc
from lemoncheesecake.reporting import Report, XmlBackend, JsonBackend, load_report, load_reports_from_dir
from lemoncheesecake.reporting.backends.xml import \
    save_report_into_file as save_xml, \
    load_report_from_file as load_xml
from lemoncheesecake.reporting.backends.json_ import \
    save_report_into_file as save_json, \
    load_report_from_file as load_json
from lemoncheesecake.reporting.backend import get_reporting_backend_names, parse_reporting_backend_names_expression
from lemoncheesecake.reporting.backends import JsonBackend
from lemoncheesecake.reporting.savingstrategy import make_report_saving_strategy

from helpers.report import assert_report
from helpers.runner import run_suite_classes


@pytest.fixture()
def sample_report():
    report = Report()
    ts = time.time()
    report.start_time = ts
    report.end_time = ts
    report.saving_time = ts
    return report


def _test_save_report(tmpdir, sample_report, backend, load_func):
    filename = tmpdir.join("report").strpath
    backend.save_report(filename, sample_report)
    report = load_func(filename)
    assert_report(report, sample_report)


def test_save_report_json(tmpdir, sample_report):
    _test_save_report(tmpdir, sample_report, JsonBackend(), load_json)


def _test_load_report(tmpdir, sample_report, save_func):
    filename = tmpdir.join("report").strpath
    save_func(sample_report, filename)
    report = load_report(filename)
    assert_report(report, sample_report)


def test_load_report_json(tmpdir, sample_report):
    _test_load_report(tmpdir, sample_report, save_json)


def test_save_loaded_report(tmpdir, sample_report):
    filename = tmpdir.join("report").strpath
    save_json(sample_report, filename)

    loaded_report = load_report(filename)
    loaded_report.end_time += 1
    loaded_report.save()

    reloaded_report = load_report(filename)
    assert reloaded_report.end_time == loaded_report.end_time


def test_load_report_xml(tmpdir, sample_report):
    _test_load_report(tmpdir, sample_report, save_xml)


def test_save_report_xml(tmpdir, sample_report):
    _test_save_report(tmpdir, sample_report, XmlBackend(), load_xml)


def test_load_reports_from_dir(tmpdir, sample_report):
    save_xml(sample_report, tmpdir.join("report.xml").strpath)
    save_json(sample_report, tmpdir.join("report.js").strpath)
    tmpdir.join("report.txt").write("foobar")
    reports = list(load_reports_from_dir(tmpdir.strpath))
    assert_report(reports[0], sample_report)
    assert_report(reports[1], sample_report)
    assert "json" in [r.backend.get_name() for r in reports]
    assert "xml" in [r.backend.get_name() for r in reports]


def _test_get_reporting_backend_names(specified, expected):
    assert get_reporting_backend_names(("console", "html", "json"), specified) == expected


def test_reporting_fixed_one():
    _test_get_reporting_backend_names(("console",), ("console",))


def test_reporting_fixed_two():
    _test_get_reporting_backend_names(("html", "json"), ("html", "json"))


def test_reporting_fixed_turn_on():
    _test_get_reporting_backend_names(("+junit",), ("console", "html", "json", "junit"))


def test_reporting_fixed_turn_off():
    _test_get_reporting_backend_names(("^console",), ("html", "json"))


def test_reporting_fixed_turn_on_and_off():
    _test_get_reporting_backend_names(("+junit", "^console"), ("html", "json", "junit"))


def test_reporting_fixed_invalid_mix():
    with pytest.raises(ValueError):
        get_reporting_backend_names(("console", "html", "json"), ("console", "+junit"))


def test_reporting_fixed_invalid_turn_off():
    with pytest.raises(ValueError):
        get_reporting_backend_names(("console", "html", "json"), ("^unknown",))


def test_parse_reporting_backend_names_expression():
    assert parse_reporting_backend_names_expression("-console  +xml  ") == ["-console", "+xml"]


@pytest.fixture()
def json_save_func_mock(mocker):
    return mocker.patch("lemoncheesecake.reporting.backends.json_.save_report_into_file")


@pytest.fixture()
def do_test_saving_strategy(json_save_func_mock):
    def func(suites, strategy_name, call_count):
        run_suite_classes(
            suites, backends=[JsonBackend()],
            report_saving_strategy=make_report_saving_strategy(strategy_name)
        )
        assert json_save_func_mock.call_count == call_count
    return func


def test_saving_strategy_at_end_of_tests(do_test_saving_strategy):
    @lcc.suite()
    class suite_1:
        @lcc.test()
        def test(self):
            pass

    do_test_saving_strategy((suite_1,), "at_end_of_tests", call_count=1)


def test_saving_strategy_at_each_suite(do_test_saving_strategy):
    @lcc.suite()
    class suite_1:
        @lcc.test()
        def test(self):
            pass

    @lcc.suite()
    class suite_2:
        @lcc.test()
        def test(self):
            pass

    do_test_saving_strategy((suite_1, suite_2), "at_each_suite", call_count=3)


def test_saving_strategy_at_each_test(do_test_saving_strategy):
    @lcc.suite()
    class suite:
        @lcc.test()
        def test_1(self):
            pass

        @lcc.test()
        def test_2(self):
            pass

        @lcc.test()
        def test_3(self):
            pass

    do_test_saving_strategy((suite,), "at_each_test", call_count=4)


def test_saving_strategy_at_each_failed_test(do_test_saving_strategy):
    @lcc.suite()
    class suite:
        @lcc.test()
        def test_1(self):
            lcc.log_error("error")

        @lcc.test()
        def test_2(self):
            pass

        @lcc.test()
        def test_3(self):
            pass

    do_test_saving_strategy((suite,), "at_each_failed_test", call_count=2)


def test_saving_strategy_at_each_log(do_test_saving_strategy):
    @lcc.suite()
    class suite:
        @lcc.test()
        def test(self):
            lcc.log_info("log 1")
            lcc.log_info("log 2")

    do_test_saving_strategy((suite,), "at_each_log", call_count=3)


def test_saving_strategy_every_N(do_test_saving_strategy):
    @lcc.suite()
    class suite:
        @lcc.test()
        def test(self):
            pass

    # this one is a very basic test because doing time-related test can be painful
    do_test_saving_strategy((suite,), "every_100s", call_count=1)
