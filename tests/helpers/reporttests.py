 # -*- coding: utf-8 -*-

'''
Created on Nov 18, 2016

@author: nicolas
'''

from __future__ import print_function

import time

import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *
from lemoncheesecake.reporting import Report
from lemoncheesecake.reporting.savingstrategy import make_report_saving_strategy

from helpers.runner import run_suite_classes
from helpers.report import assert_report, report_in_progress
from helpers.utils import change_dir


class ReportingSessionTests(object):
    backend = NotImplemented

    # for every tests in this class (and the base class), the current working directory will be a temporary directory
    # where it can freely write any file
    @pytest.fixture(autouse=True)
    def prepare_work_dir(self, tmpdir):
        with change_dir(tmpdir.strpath):
            yield

    def do_test_reporting_session(self, suites, fixtures=(), report_saving_strategy=None, nb_threads=1):
        raise NotImplementedError()

    def test_simple_test(self, report_saving_strategy=None):
        @lcc.suite("MySuite")
        class MySuite:
            def setup_suite(self):
                # make sure that the saving strategy also works well with
                # a end-type event but no result
                pass

            @lcc.test("Some test")
            def sometest(self):
                check_that("foo", 1, equal_to(1))

        self.do_test_reporting_session(MySuite)

    def test_test_with_all_metadata(self):
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.link("http://foo.bar", "foobar")
            @lcc.prop("foo", "bar")
            @lcc.tags("foo", "bar")
            @lcc.test("Some test")
            def sometest(self):
                check_that("foo", 1, equal_to(1))

        self.do_test_reporting_session(MySuite)

    def test_suite_with_all_metadata(self):
        @lcc.link("http://foo.bar", "foobar")
        @lcc.prop("foo", "bar")
        @lcc.tags("foo", "bar")
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Some test")
            def sometest(self):
                check_that("foo", 1, equal_to(1))

        self.do_test_reporting_session(MySuite)

    def test_link_without_name(self):
        @lcc.suite("MySuite")
        @lcc.link("http://foo.bar")
        class MySuite:
            @lcc.test("Some test")
            @lcc.link("http://foo.bar")
            def sometest(self):
                pass

        self.do_test_reporting_session(MySuite)

    def test_unicode(self):
        @lcc.link("http://foo.bar", "éééààà")
        @lcc.prop("ééé", "ààà")
        @lcc.tags("ééé", "ààà")
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.link("http://foo.bar", "éééààà")
            @lcc.prop("ééé", "ààà")
            @lcc.tags("ééé", "ààà")
            @lcc.test("Some test ààà")
            def sometest(self):
                lcc.set_step("éééààà")
                check_that("éééààà", 1, equal_to(1))
                lcc.log_info("éééààà")
                lcc.save_attachment_content("A" * 1024, "somefileààà", "éééààà")
                lcc.log_url("http://example.com", "example")

        self.do_test_reporting_session(MySuite)

    def test_multiple_suites_and_tests(self):
        @lcc.suite("MySuite1")
        class MySuite1:
            @lcc.tags("foo")
            @lcc.test("Some test 1")
            def test_1_1(self):
                check_that("foo", 2, equal_to(2))

            @lcc.tags("bar")
            @lcc.test("Some test 2")
            def test_1_2(self):
                check_that("foo", 2, equal_to(2))

            @lcc.tags("baz")
            @lcc.test("Some test 3")
            def test_1_3(self):
                check_that("foo", 3, equal_to(2))

        @lcc.suite("MySuite2")
        class MySuite2:
            @lcc.prop("foo", "bar")
            @lcc.test("Some test 1")
            def test_2_1(self):
                1 / 0

            @lcc.prop("foo", "baz")
            @lcc.test("Some test 2")
            def test_2_2(self):
                check_that("foo", 2, equal_to(2))

            @lcc.test("Some test 3")
            def test_2_3(self):
                check_that("foo", 2, equal_to(2))

            # suite3 is a sub suite of suite3
            @lcc.suite("MySuite3")
            class MySuite3:
                @lcc.prop("foo", "bar")
                @lcc.test("Some test 1")
                def test_3_1(self):
                    check_that("foo", 1, equal_to(1))

                @lcc.prop("foo", "baz")
                @lcc.test("Some test 2")
                def test_3_2(self):
                    raise lcc.AbortTest("")

                @lcc.test("Some test 3")
                def test_3_3(self):
                    check_that("foo", 1, equal_to(1))

        self.do_test_reporting_session((MySuite1, MySuite2))

    def test_check_success(self):
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Test 1")
            def test_1(self):
                check_that("somevalue", "foo", equal_to("foo"))

        self.do_test_reporting_session(MySuite)

    def test_check_failure(self):
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Test 1")
            def test_1(self):
                check_that("somevalue", "foo", equal_to("bar"))

        self.do_test_reporting_session(MySuite)

    def test_require_success(self):
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Test 1")
            def test_1(self):
                require_that("somevalue", "foo", equal_to("foo"))

        self.do_test_reporting_session(MySuite)

    def test_require_failure(self):
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Test 1")
            def test_1(self):
                require_that("somevalue", "foo", equal_to("bar"))

        self.do_test_reporting_session(MySuite)

    def test_assert_failure(self):
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Test 1")
            def test_1(self):
                assert_that("somevalue", "foo", equal_to("bar"))

        self.do_test_reporting_session(MySuite)

    def test_all_types_of_logs(self):
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Test 1")
            def test_1(self):
                lcc.log_debug("some debug message")
                lcc.log_info("some info message")
                lcc.log_warning("some warning message")

            @lcc.test("Test 2")
            def test_2(self):
                lcc.log_error("some error message")

        self.do_test_reporting_session(MySuite)

    def test_multiple_steps(self):
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Some test")
            def sometest(self):
                lcc.set_step("step 1")
                lcc.log_info("do something")
                lcc.set_step("step 2")
                lcc.log_info("do something else")

        self.do_test_reporting_session(MySuite)

    def test_attachment(self):
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Some test")
            def sometest(self):
                lcc.save_attachment_content("foobar", "foobar.txt")

        self.do_test_reporting_session(MySuite)

    def test_image(self):
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Some test")
            def sometest(self):
                lcc.save_image_content("foobar", "foobar.txt")  # not actual image content, but it does not matter here

        self.do_test_reporting_session(MySuite)

    def test_log_url(self):
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Some test")
            def sometest(self):
                lcc.log_url("http://www.example.com", "example")

        self.do_test_reporting_session(MySuite)

    def test_setup_suite_success(self):
        @lcc.suite("MySuite")
        class MySuite:
            def setup_suite(self):
                lcc.log_info("some log")

            @lcc.test("Some test")
            def sometest(self):
                pass

        self.do_test_reporting_session(MySuite)

    def test_setup_suite_failure(self):
        @lcc.suite("MySuite")
        class MySuite:
            def setup_suite(self):
                lcc.log_error("something bad happened")

            @lcc.test("Some test")
            def sometest(self):
                pass

        self.do_test_reporting_session(MySuite)

    # reproduce a bug introduced in 3e4d341
    def test_setup_suite_nested(self):
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.suite("MySubSuite")
            class MySubSuite:
                def setup_suite(self):
                    lcc.log_info("some log")

                @lcc.test("Some test")
                def sometest(self):
                    pass

        self.do_test_reporting_session(MySuite)

    def test_teardown_suite_success(self):
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Some test")
            def sometest(self):
                pass

            def teardown_suite(self):
                lcc.log_info("some log")

        self.do_test_reporting_session(MySuite)

    def test_teardown_suite_failure(self):
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Some test")
            def sometest(self):
                pass

            def teardown_suite(self):
                lcc.log_error("something bad happened")

        self.do_test_reporting_session(MySuite)

    def test_setup_and_teardown_suite(self):
        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Some test")
            def sometest(self):
                pass

            def setup_suite(self):
                lcc.log_info("some log")

            def teardown_suite(self):
                lcc.log_info("some other log")

        self.do_test_reporting_session(MySuite)

    def test_setup_test_session_success(self):
        @lcc.fixture(scope="session")
        def fixt():
            lcc.log_info("some log")

        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Some test")
            def sometest(self, fixt):
                pass

        self.do_test_reporting_session(MySuite, fixtures=[fixt])

    def test_setup_test_session_failure(self):
        @lcc.fixture(scope="session")
        def fixt():
            lcc.log_error("some error")

        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Some test")
            def sometest(self, fixt):
                pass

        self.do_test_reporting_session(MySuite, fixtures=[fixt])

    def test_teardown_test_session_success(self):
        @lcc.fixture(scope="session")
        def fixt():
            yield
            lcc.log_info("some info")

        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Some test")
            def sometest(self, fixt):
                pass

        self.do_test_reporting_session(MySuite, fixtures=[fixt])

    def test_teardown_test_session_failure(self):
        @lcc.fixture(scope="session")
        def fixt():
            yield
            lcc.log_error("some error")

        @lcc.suite("MySuite")
        class MySuite:
            @lcc.test("Some test")
            def sometest(self, fixt):
                pass

        self.do_test_reporting_session(MySuite, fixtures=[fixt])

    def test_setup_and_teardown_test_session(self):
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

        self.do_test_reporting_session(MySuite, fixtures=[fixt])

    # TODO: see below, the behavior of each save mode is not tested in fact, but
    # at least we want to make sure that each of this mode is not failing

    def test_save_at_end_of_tests(self):
        self.test_simple_test(None)

    def test_save_at_each_log(self):
        self.test_simple_test(make_report_saving_strategy("at_each_log"))

    def test_save_at_each_event(self):
        # "at_each_event" has been deprecated in 1.4.5 and replaced by at_each_log
        self.test_simple_test(make_report_saving_strategy("at_each_event"))

    def test_save_at_each_failed_test(self):
        self.test_simple_test(make_report_saving_strategy("at_each_failed_test"))

    def test_save_at_each_test(self):
        self.test_simple_test(make_report_saving_strategy("at_each_test"))

    def test_save_at_each_suite(self):
        self.test_simple_test(make_report_saving_strategy("at_each_suite"))

    def test_save_every_seconds(self):
        self.test_simple_test(make_report_saving_strategy("every_1s"))

    def test_parallelized_tests(self):
        @lcc.suite("Suite")
        class suite:
            @lcc.test("Test 1")
            def test_1(self):
                lcc.log_info("some log")

            @lcc.test("Test 2")
            def test_2(self):
                lcc.log_info("some other log")

        self.do_test_reporting_session(suite, nb_threads=2)


class ReportSerializationTests(ReportingSessionTests):
    def do_test_reporting_session(self, suites, fixtures=(), report_saving_strategy=None, nb_threads=1):
        if type(suites) not in (list, tuple):
            suites = [suites]
        report = run_suite_classes(
            suites, fixtures=fixtures, backends=(self.backend,), tmpdir=".",
            report_saving_strategy=report_saving_strategy, nb_threads=nb_threads
        )
        unserialized_report = self.backend.load_report(self.backend.get_report_filename())
        assert_report(unserialized_report, report)

    def do_test_report_serialization(self, report):
        self.backend.save_report("report", report)
        unserialized_report = self.backend.load_report("report")
        assert_report(unserialized_report, report)

    def test_report_title(self):
        report = Report()
        report.title = "Report Title"
        report.start_time = time.time()
        report.end_time = report.start_time
        report.saving_time = report.start_time

        self.do_test_report_serialization(report)

    def test_nb_threads(self):
        report = Report()
        report.nb_threads = 3
        report.start_time = time.time()
        report.end_time = report.start_time
        report.saving_time = report.start_time

        self.do_test_report_serialization(report)

    def test_report_in_progress(self, report_in_progress):
        self.do_test_report_serialization(report_in_progress)
