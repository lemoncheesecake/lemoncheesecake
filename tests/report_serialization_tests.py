 # -*- coding: utf-8 -*-

'''
Created on Nov 18, 2016

@author: nicolas
'''

from __future__ import print_function

import time

import lemoncheesecake.api as lcc
from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.reporting.backend import SAVE_AT_EACH_EVENT, SAVE_AT_EACH_FAILED_TEST, \
    SAVE_AT_EACH_TEST, SAVE_AT_EACH_SUITE, SAVE_AT_END_OF_TESTS
from lemoncheesecake.reporting import Report

from helpers import run_suite_class, run_suite_classes, assert_report, dump_report


def do_test_serialization(suites, backend, tmpdir, fixtures=[]):
    if type(suites) in (list, tuple):
        run_suite_classes(suites, fixtures=fixtures, backends=[backend])
    else:
        run_suite_class(suites, fixtures=fixtures, backends=[backend])

    report = get_runtime().report

    report_filename = tmpdir.join("report").strpath
    backend.save_report(report_filename, report)
    unserialized_report = backend.load_report(report_filename)

#     dump_report(unserialized_report)

    assert_report(unserialized_report, report)


def test_simple_test(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_that("foo", 1, lcc.equal_to(1))

    do_test_serialization(MySuite, backend, tmpdir)


def test_test_with_all_metadata(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.link("http://foo.bar", "foobar")
        @lcc.prop("foo", "bar")
        @lcc.tags("foo", "bar")
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_that("foo", 1, lcc.equal_to(1))

    do_test_serialization(MySuite, backend, tmpdir)


def test_suite_with_all_metadata(backend, tmpdir):
    @lcc.link("http://foo.bar", "foobar")
    @lcc.prop("foo", "bar")
    @lcc.tags("foo", "bar")
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.check_that("foo", 1, lcc.equal_to(1))

    do_test_serialization(MySuite, backend, tmpdir)


def test_unicode(backend, tmpdir):
    @lcc.link("http://foo.bar", u"éééààà")
    @lcc.prop(u"ééé", u"ààà")
    @lcc.tags(u"ééé", u"ààà")
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.link("http://foo.bar", u"éééààà")
        @lcc.prop(u"ééé", u"ààà")
        @lcc.tags(u"ééé", u"ààà")
        @lcc.test(u"Some test ààà")
        def sometest(self):
            lcc.set_step(u"éééààà")
            lcc.check_that(u"éééààà", 1, lcc.equal_to(1))
            lcc.log_info(u"éééààà")
            lcc.save_attachment_content("A" * 1024, u"somefileààà", u"éééààà")
            lcc.log_url("http://example.com", "example")

    do_test_serialization(MySuite, backend, tmpdir)


def test_multiple_suites_and_tests(backend, tmpdir):
    @lcc.suite("MySuite1")
    class MySuite1:
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
    class MySuite2:
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

        # suite3 is a sub suite of suite3
        @lcc.suite("MySuite3")
        class MySuite3:
            @lcc.prop("foo", "bar")
            @lcc.test("Some test 1")
            def test_3_1(self):
                lcc.check_that("foo", 1, lcc.equal_to(1))

            @lcc.prop("foo", "baz")
            @lcc.test("Some test 2")
            def test_3_2(self):
                raise lcc.AbortTest()

            @lcc.test("Some test 3")
            def test_3_3(self):
                lcc.check_that("foo", 1, lcc.equal_to(1))

    do_test_serialization((MySuite1, MySuite2), backend, tmpdir)


def test_check_success(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.check_that("somevalue", "foo", lcc.equal_to("foo"))

    do_test_serialization(MySuite, backend, tmpdir)


def test_check_failure(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.check_that("somevalue", "foo", lcc.equal_to("bar"))

    do_test_serialization(MySuite, backend, tmpdir)


def test_require_success(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.require_that("somevalue", "foo", lcc.equal_to("foo"))

    do_test_serialization(MySuite, backend, tmpdir)


def test_require_failure(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.require_that("somevalue", "foo", lcc.equal_to("bar"))

    do_test_serialization(MySuite, backend, tmpdir)


def test_assert_failure(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.assert_that("somevalue", "foo", lcc.equal_to("bar"))

    do_test_serialization(MySuite, backend, tmpdir)


def test_all_types_of_logs(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.log_debug("some debug message")
            lcc.log_info("some info message")
            lcc.log_warn("some warning message")

        @lcc.test("Test 2")
        def test_2(self):
            lcc.log_error("some error message")

    do_test_serialization(MySuite, backend, tmpdir)


def test_multiple_steps(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.set_step("step 1")
            lcc.log_info("do something")
            lcc.set_step("step 2")
            lcc.log_info("do something else")

    do_test_serialization(MySuite, backend, tmpdir)


def test_attachment(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.save_attachment_content("foobar", "foobar.txt")

    do_test_serialization(MySuite, backend, tmpdir)


def test_log_url(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.log_url("http://www.example.com", "example")

    do_test_serialization(MySuite, backend, tmpdir)


def test_setup_suite_success(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        def setup_suite(self):
            lcc.log_info("some log")

        @lcc.test("Some test")
        def sometest(self):
            pass

    do_test_serialization(MySuite, backend, tmpdir)


def test_setup_suite_failure(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        def setup_suite(self):
            lcc.log_error("something bad happened")

        @lcc.test("Some test")
        def sometest(self):
            pass

    do_test_serialization(MySuite, backend, tmpdir)


# reproduce a bug introduced in 3e4d341
def test_setup_suite_nested(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.suite("MySubSuite")
        class MySubSuite:
            def setup_suite(self):
                lcc.log_info("some log")

            @lcc.test("Some test")
            def sometest(self):
                pass

    do_test_serialization(MySuite, backend, tmpdir)


def test_teardown_suite_success(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            lcc.log_info("some log")

    do_test_serialization(MySuite, backend, tmpdir)


def test_teardown_suite_failure(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            lcc.log_error("something bad happened")

    do_test_serialization(MySuite, backend, tmpdir)


def test_setup_and_teardown_suite(backend, tmpdir):
    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def setup_suite(self):
            lcc.log_info("some log")

        def teardown_suite(self):
            lcc.log_info("some other log")

    do_test_serialization(MySuite, backend, tmpdir)


def test_setup_test_session_success(backend, tmpdir):
    @lcc.fixture(scope="session")
    def fixt():
        lcc.log_info("some log")

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    do_test_serialization(MySuite, backend, tmpdir, fixtures=[fixt])


def test_setup_test_session_failure(backend, tmpdir):
    @lcc.fixture(scope="session")
    def fixt():
        lcc.log_error("some error")

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    do_test_serialization(MySuite, backend, tmpdir, fixtures=[fixt])


def test_teardown_test_session_success(backend, tmpdir):
    @lcc.fixture(scope="session")
    def fixt():
        yield
        lcc.log_info("some info")

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    do_test_serialization(MySuite, backend, tmpdir, fixtures=[fixt])


def test_teardown_test_session_failure(backend, tmpdir):
    @lcc.fixture(scope="session")
    def fixt():
        yield
        lcc.log_error("some error")

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    do_test_serialization(MySuite, backend, tmpdir, fixtures=[fixt])


def test_setup_and_teardown_test_session(backend, tmpdir):
    @lcc.fixture(scope="session")
    def fixt():
        lcc.log_info("some info")
        yield
        lcc.log_info("some other info")

    @lcc.suite("MySuite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    do_test_serialization(MySuite, backend, tmpdir, fixtures=[fixt])


def test_report_title(backend, tmpdir):
    report = Report()
    report.title = "Report Title"
    report.start_time = time.time()
    report.end_time = report.start_time
    report.report_generation_time = report.start_time

    report_filename = tmpdir.join("report").strpath
    backend.save_report(report_filename, report)
    unserialized_report = backend.load_report(report_filename)

#    dump_report(unserialized_report)

    assert_report(unserialized_report, report)


# TODO: see below, the behavior of each save mode is not tested in fact, but
# at least we want to make sure that each of this mode is not failing

def test_save_at_end_of_tests(backend, tmpdir):
    backend.save_mode = SAVE_AT_END_OF_TESTS
    test_simple_test(backend, tmpdir)


def test_save_at_end_of_each_event(backend, tmpdir):
    backend.save_mode = SAVE_AT_EACH_EVENT
    test_simple_test(backend, tmpdir)


def test_save_at_each_failed_test(backend, tmpdir):
    backend.save_mode = SAVE_AT_EACH_FAILED_TEST
    test_simple_test(backend, tmpdir)


def test_save_at_each_test(backend, tmpdir):
    backend.save_mode = SAVE_AT_EACH_TEST
    test_simple_test(backend, tmpdir)


def test_save_at_each_suite(backend, tmpdir):
    backend.save_mode = SAVE_AT_EACH_SUITE
    test_simple_test(backend, tmpdir)
