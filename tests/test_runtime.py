 # -*- coding: utf-8 -*-

'''
Created on Nov 1, 2016

@author: nicolas
'''

import os.path

import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.testtree import find_test, find_suite
from lemoncheesecake.exceptions import ProgrammingError

from helpers.runner import run_suite_class, run_suite_classes
from helpers.report import assert_report_from_suite, assert_report_from_suites, assert_report_stats, \
    assert_test_passed, assert_test_failed, assert_test_skipped, assert_test_statuses


def test_simple_test():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_that("foo", 1, lcc.equal_to(1))

    run_suite_class(mysuite)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1, expected_check_successes=1)

    assert_test_passed(report, "mysuite.sometest")


def test_test_with_all_metadata():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.link("http://foo.bar", "foobar")
        @lcc.prop("foo", "bar")
        @lcc.tags("foo", "bar")
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_that("foo", 1, lcc.equal_to(1))

    run_suite_class(mysuite)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1, expected_check_successes=1)

    assert_test_passed(report, "mysuite.sometest")


def test_suite_with_all_metadata():
    @lcc.link("http://foo.bar", "foobar")
    @lcc.prop("foo", "bar")
    @lcc.tags("foo", "bar")
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_that("foo", 1, lcc.equal_to(1))

    run_suite_class(mysuite)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1, expected_check_successes=1)

    assert_test_passed(report, "mysuite.sometest")


def test_multiple_suites_and_tests():
    @lcc.suite("MySuite1")
    class mysuite1:
        @lcc.tags("foo")
        @lcc.test("Some test 1")
        def test_1_1(self):
            lcc.check_that("foo", 2, lcc.equal_to(2))

        @lcc.tags("bar")
        @lcc.test("Some test 2")
        def test_1_2(self):
            lcc.check_that("foo", 2, lcc.equal_to(2))

        @lcc.tags("baz")
        @lcc.test("Some test 3")
        def test_1_3(self):
            lcc.check_that("foo", 3, lcc.equal_to(2))

    @lcc.suite("MySuite2")
    class mysuite2:
        @lcc.prop("foo", "bar")
        @lcc.test("Some test 1")
        def test_2_1(self):
            1 / 0

        @lcc.prop("foo", "baz")
        @lcc.test("Some test 2")
        def test_2_2(self):
            lcc.check_that("foo", 2, lcc.equal_to(2))

        @lcc.test("Some test 3")
        def test_2_3(self):
            lcc.check_that("foo", 2, lcc.equal_to(2))

        # suite3 is a sub suite of suite2
        @lcc.suite("MySuite3")
        class mysuite3:
            @lcc.prop("foo", "bar")
            @lcc.test("Some test 1")
            def test_3_1(self):
                lcc.check_that("foo", 1, lcc.equal_to(1))

            @lcc.prop("foo", "baz")
            @lcc.test("Some test 2")
            def test_3_2(self):
                raise lcc.AbortTest("error")

            @lcc.test("Some test 3")
            def test_3_3(self):
                lcc.check_that("foo", 1, lcc.equal_to(1))

    run_suite_classes([mysuite1, mysuite2])

    report = get_runtime().report

    assert_report_from_suites(report, [mysuite1, mysuite2])
    assert_report_stats(
        report,
        expected_test_successes=6, expected_test_failures=3,
        expected_check_successes=6, expected_check_failures=1, expected_error_logs=2
    )

    assert_test_statuses(
        report,
        passed=(
            "mysuite1.test_1_1", "mysuite1.test_1_2", "mysuite2.test_2_2",
            "mysuite2.test_2_3", "mysuite2.mysuite3.test_3_1", "mysuite2.mysuite3.test_3_3"
        ),
        failed=("mysuite1.test_1_3", "mysuite2.test_2_1", "mysuite2.mysuite3.test_3_2")
    )


def test_check_success():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.check_that("somevalue", "foo", lcc.equal_to("foo"))

    run_suite_class(mysuite)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1, expected_check_successes=1)

    test = find_test(report.suites, "mysuite.test_1")
    assert test.status == "passed"
    step = test.steps[0]
    assert "somevalue" in step.entries[0].description
    assert "foo" in step.entries[0].description
    assert step.entries[0].outcome == True
    assert "foo" in step.entries[0].details


def test_check_failure():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.check_that("somevalue", "foo", lcc.equal_to("bar"))

    run_suite_class(mysuite)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_failures=1, expected_check_failures=1)

    test = find_test(report.suites, "mysuite.test_1")
    assert test.status == "failed"
    step = test.steps[0]
    assert "somevalue" in step.entries[0].description
    assert "bar" in step.entries[0].description
    assert step.entries[0].outcome == False
    assert "foo" in step.entries[0].details


def test_require_success():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.require_that("somevalue", "foo", lcc.equal_to("foo"))

    run_suite_class(mysuite)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1, expected_check_successes=1)

    test = find_test(report.suites, "mysuite.test_1")
    assert test.status == "passed"
    step = test.steps[0]
    assert "somevalue" in step.entries[0].description
    assert "foo" in step.entries[0].description
    assert step.entries[0].outcome == True
    assert "foo" in step.entries[0].details


def test_require_failure():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.require_that("somevalue", "foo", lcc.equal_to("bar"))

    run_suite_class(mysuite)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_failures=1, expected_check_failures=1, expected_error_logs=1)

    test = find_test(report.suites, "mysuite.test_1")
    assert test.status == "failed"
    step = test.steps[0]
    assert "somevalue" in step.entries[0].description
    assert "bar" in step.entries[0].description
    assert step.entries[0].outcome == False
    assert "foo" in step.entries[0].details


def test_all_types_of_logs():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.log_debug("some debug message")
            lcc.log_info("some info message")
            lcc.log_warn("some warning message")

        @lcc.test("Test 2")
        def test_2(self):
            lcc.log_error("some error message")

    run_suite_class(mysuite)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report,
        expected_test_successes=1, expected_test_failures=1,
        expected_error_logs=1, expected_warning_logs=1
    )

    test = find_test(report.suites, "mysuite.test_1")
    assert test.status == "passed"
    step = test.steps[0]
    assert step.entries[0].level == "debug"
    assert step.entries[0].message == "some debug message"
    assert step.entries[1].level == "info"
    assert step.entries[1].message == "some info message"
    assert step.entries[2].level == "warn"

    test = find_test(report.suites, "mysuite.test_2")
    assert test.status == "failed"
    step = test.steps[0]
    assert step.entries[0].message == "some error message"
    assert step.entries[0].level == "error"


def test_multiple_steps():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.set_step("step 1")
            lcc.log_info("do something")
            lcc.set_step("step 2")
            lcc.log_info("do something else")

    run_suite_class(mysuite)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1)

    test = find_test(report.suites, "mysuite.sometest")
    assert test.status == "passed"
    assert test.steps[0].description == "step 1"
    assert test.steps[0].entries[0].level == "info"
    assert test.steps[0].entries[0].message == "do something"
    assert test.steps[1].description == "step 2"
    assert test.steps[1].entries[0].level == "info"
    assert test.steps[1].entries[0].message == "do something else"


def test_default_step():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.log_info("do something")

    run_suite_class(mysuite)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1)

    test = find_test(report.suites, "mysuite.sometest")
    assert test.status == "passed"
    assert test.steps[0].description == "Some test"
    assert test.steps[0].entries[0].level == "info"
    assert test.steps[0].entries[0].message == "do something"


def test_step_after_test_setup():
    @lcc.suite("mysuite")
    class mysuite:
        def setup_test(self, test_name):
            lcc.log_info("in test setup")

        @lcc.test("Some test")
        def sometest(self):
            lcc.log_info("do something")

    run_suite_class(mysuite)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1)

    test = find_test(report.suites, "mysuite.sometest")
    assert test.status == "passed"
    assert test.steps[0].description == "Setup test"
    assert test.steps[0].entries[0].level == "info"
    assert test.steps[0].entries[0].message == "in test setup"
    assert test.steps[1].description == "Some test"
    assert test.steps[1].entries[0].level == "info"
    assert test.steps[1].entries[0].message == "do something"


def test_prepare_attachment(tmpdir):
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            with lcc.prepare_attachment("foobar.txt", "some description") as filename:
                with open(filename, "w") as fh:
                    fh.write("some content")

    run_suite_class(mysuite, tmpdir=tmpdir)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1)

    test = find_test(report.suites, "mysuite.sometest")
    assert test.steps[0].entries[0].filename.endswith("foobar.txt")
    assert test.steps[0].entries[0].description == "some description"
    assert test.status == "passed"
    with open(os.path.join(get_runtime().report_dir, test.steps[0].entries[0].filename)) as fh:
        assert fh.read() == "some content"


def test_save_attachment_file(tmpdir):
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            filename = os.path.join(tmpdir.strpath, "somefile.txt")
            with open(filename, "w") as fh:
                fh.write("some other content")
            lcc.save_attachment_file(filename, "some other file")

    run_suite_class(mysuite, tmpdir=tmpdir.mkdir("report"))

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1)

    test = find_test(report.suites, "mysuite.sometest")
    assert test.steps[0].entries[0].filename.endswith("somefile.txt")
    assert test.steps[0].entries[0].description == "some other file"
    assert test.status == "passed"
    with open(os.path.join(get_runtime().report_dir, test.steps[0].entries[0].filename)) as fh:
        assert fh.read() == "some other content"


def _test_save_attachment_content(tmpdir, file_name, file_content, encoding=None):
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.save_attachment_content(file_content, file_name, binary_mode=not encoding)

    run_suite_class(mysuite, tmpdir=tmpdir)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1)

    test = find_test(report.suites, "mysuite.sometest")
    assert test.steps[0].entries[0].filename.endswith(file_name)
    assert test.steps[0].entries[0].description == file_name
    assert test.status == "passed"
    with open(os.path.join(get_runtime().report_dir, test.steps[0].entries[0].filename), "rb") as fh:
        actual_content = fh.read()
    if encoding != None:
        actual_content = actual_content.decode(encoding)
    assert actual_content == file_content


def test_save_attachment_text_ascii(tmpdir):
    _test_save_attachment_content(tmpdir, "foobar.txt", "foobar", encoding="ascii")


def test_save_attachment_text_utf8(tmpdir):
    _test_save_attachment_content(tmpdir, "foobar.txt", u"éééçççààà", encoding="utf-8")


def test_save_attachment_binary(tmpdir):
    p = os.path
    with open(p.join(p.dirname(__file__), p.pardir, "misc", "report-screenshot.png"), "rb") as fh:
        content = fh.read()
    _test_save_attachment_content(tmpdir, "foobar.png", content)


def test_log_url():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.log_url("http://example.com", "example")

    run_suite_class(mysuite)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1)

    test = find_test(report.suites, "mysuite.sometest")

    assert test.steps[0].entries[0].description == "example"
    assert test.steps[0].entries[0].url == "http://example.com"


def test_unicode(tmpdir):
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("some test")
        def sometest(self):
            lcc.set_step(u"éééààà")
            lcc.check_that(u"éééààà", 1, lcc.equal_to(1))
            lcc.log_info(u"éééààà")
            lcc.save_attachment_content("A" * 1024, u"somefileààà", u"éééààà")

    run_suite_class(mysuite, tmpdir=tmpdir)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1, expected_check_successes=1)

    test = find_test(report.suites, "mysuite.sometest")
    assert test.status == "passed"
    step = test.steps[0]
    assert step.description == u"éééààà"
    assert u"éééààà" in step.entries[0].description
    assert "1" in step.entries[0].description
    assert step.entries[1].message == u"éééààà"
    assert step.entries[2].filename.endswith(u"somefileààà")
    assert step.entries[2].description == u"éééààà"
    with open(os.path.join(get_runtime().report_dir, step.entries[2].filename)) as fh:
        assert fh.read() == "A" * 1024


def test_setup_suite_success():
    @lcc.suite("MySuite")
    class mysuite:
        def setup_suite(self):
            lcc.log_info("some log")

        @lcc.test("Some test")
        def sometest(self):
            pass

    run_suite_class(mysuite)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1)

    suite = find_suite(report.suites, "mysuite")
    assert suite.suite_setup.outcome == True
    assert suite.suite_setup.start_time != None
    assert suite.suite_setup.end_time != None
    assert suite.suite_setup.steps[0].entries[0].message == "some log"
    assert suite.suite_setup.has_failure() == False
    assert_test_passed(report, "mysuite.sometest")


def test_setup_suite_failure():
    @lcc.suite("MySuite")
    class mysuite:
        def setup_suite(self):
            lcc.log_error("something bad happened")

        @lcc.test("Some test")
        def sometest(self):
            pass

    run_suite_class(mysuite)

    report = get_runtime().report

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_skippeds=1, expected_errors=1, expected_error_logs=1)

    suite = find_suite(report.suites, "mysuite")
    assert suite.suite_setup.outcome == False
    assert suite.suite_setup.start_time != None
    assert suite.suite_setup.end_time != None
    assert suite.suite_setup.steps[0].entries[0].message == "something bad happened"
    assert suite.suite_setup.has_failure() == True
    assert_test_skipped(report, "mysuite.sometest")


def test_setup_suite_without_content():
    marker = []

    @lcc.suite("MySuite")
    class mysuite:
        def setup_suite(self):
            marker.append("setup")

        @lcc.test("Some test")
        def sometest(self):
            pass

    run_suite_class(mysuite)

    report = get_runtime().report

    assert report.suites[0].suite_setup == None
    assert marker == ["setup"]


def test_teardown_suite_success():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            lcc.log_info("some log")

    report = run_suite_class(mysuite)

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1)

    suite = find_suite(report.suites, "mysuite")
    assert suite.suite_teardown.outcome == True
    assert suite.suite_teardown.start_time != None
    assert suite.suite_teardown.end_time != None
    assert suite.suite_teardown.steps[0].entries[0].message == "some log"
    assert suite.suite_teardown.has_failure() == False
    assert_test_passed(report, "mysuite.sometest")


def test_teardown_suite_failure():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            lcc.check_that("val", 1, lcc.equal_to(2))

    report = run_suite_class(mysuite)

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1, expected_errors=1, expected_check_failures=1)

    suite = find_suite(report.suites, "mysuite")
    assert suite.suite_teardown.outcome == False
    assert suite.suite_teardown.start_time != None
    assert suite.suite_teardown.end_time != None
    assert suite.suite_teardown.steps[0].entries[0].outcome == False
    assert suite.suite_teardown.has_failure() == True
    assert_test_passed(report, "mysuite.sometest")


def test_teardown_suite_without_content():
    marker = []

    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            marker.append("teardown")

    report = run_suite_class(mysuite)

    assert report.suites[0].suite_teardown == None
    assert marker == ["teardown"]


def test_setup_test_session_success():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    @lcc.fixture(scope="session")
    def fixt():
        lcc.log_info("some log")

    report = run_suite_class(mysuite, fixtures=[fixt])

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1)

    assert report.test_session_setup.outcome == True
    assert report.test_session_setup.start_time != None
    assert report.test_session_setup.end_time != None
    assert report.test_session_setup.steps[0].entries[0].message == "some log"
    assert report.test_session_setup.has_failure() == False
    assert_test_passed(report, "mysuite.sometest")


def test_setup_test_session_failure():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    @lcc.fixture(scope="session")
    def fixt():
        lcc.log_error("something bad happened")

    report = run_suite_class(mysuite, fixtures=[fixt])

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_skippeds=1, expected_errors=1, expected_error_logs=1)

    assert report.test_session_setup.outcome == False
    assert report.test_session_setup.start_time != None
    assert report.test_session_setup.end_time != None
    assert report.test_session_setup.steps[0].entries[0].message == "something bad happened"
    assert report.test_session_setup.has_failure() == True
    assert_test_skipped(report, "mysuite.sometest")


def test_setup_test_session_without_content():
    marker = []

    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    @lcc.fixture(scope="session")
    def fixt():
        marker.append("setup")

    report = run_suite_class(mysuite, fixtures=[fixt])

    assert report.test_session_setup == None
    assert marker == ["setup"]


def test_teardown_test_session_success():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    @lcc.fixture(scope="session")
    def fixt():
        yield
        lcc.log_info("some log")

    report = run_suite_class(mysuite, fixtures=[fixt])

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1)

    assert report.test_session_teardown.outcome == True
    assert report.test_session_teardown.start_time != None
    assert report.test_session_teardown.end_time != None
    assert report.test_session_teardown.steps[0].entries[0].message == "some log"
    assert report.test_session_teardown.has_failure() == False
    assert_test_passed(report, "mysuite.sometest")


def test_teardown_test_session_failure():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    @lcc.fixture(scope="session")
    def fixt():
        yield
        lcc.check_that("val", 1, lcc.equal_to(2))

    report = run_suite_class(mysuite, fixtures=[fixt])

    assert_report_from_suite(report, mysuite)
    assert_report_stats(report, expected_test_successes=1, expected_errors=1, expected_check_failures=1)

    assert report.test_session_teardown.outcome == False
    assert report.test_session_teardown.start_time != None
    assert report.test_session_teardown.end_time != None
    assert report.test_session_teardown.steps[0].entries[0].outcome == False
    assert report.test_session_teardown.has_failure() == True
    assert_test_passed(report, "mysuite.sometest")


def test_teardown_test_session_without_content():
    marker = []

    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    @lcc.fixture(scope="session")
    def fixt():
        yield
        marker.append("teardown")

    report = run_suite_class(mysuite, fixtures=[fixt])

    assert report.test_session_teardown == None
    assert marker == ["teardown"]


def test_add_report_info():
    @lcc.suite("Some suite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.add_report_info("some info", "some data")

    report = run_suite_class(mysuite)

    assert report.info[-1] == ["some info", "some data"]


def test_get_fixture():
    @lcc.fixture(scope="session_prerun")
    def fixt():
        return 42

    @lcc.suite("mysuite")
    class mysuite:
        @lcc.test("mytest")
        def mytest(self, fixt):
            assert lcc.get_fixture("fixt") == 42

    report = run_suite_class(mysuite, fixtures=[fixt])

    assert_report_stats(report, expected_test_successes=1)


def test_get_fixture_bad_scope():
    @lcc.fixture(scope="test")
    def fixt():
        return 42

    @lcc.suite("mysuite")
    class mysuite:
        @lcc.test("mytest")
        def mytest(self, fixt):
            with pytest.raises(ProgrammingError):
                lcc.get_fixture("fixt")

    report = run_suite_class(mysuite, fixtures=[fixt])

    assert_report_stats(report, expected_test_successes=1)


def test_get_fixture_unknown():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.test("mytest")
        def mytest(self):
            with pytest.raises(ProgrammingError):
                lcc.get_fixture("fixt")

    report = run_suite_class(mysuite)

    assert_report_stats(report, expected_test_successes=1)


def test_get_fixture_not_executed():
    @lcc.fixture(scope="session_prerun")
    def fixt():
        return 42

    @lcc.suite("mysuite")
    class mysuite:
        @lcc.test("mytest")
        def mytest(self):
            with pytest.raises(ProgrammingError):
                lcc.get_fixture("fixt")

    report = run_suite_class(mysuite, fixtures=[fixt])

    assert_report_stats(report, expected_test_successes=1)
