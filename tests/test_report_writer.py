# -*- coding: utf-8 -*-

'''
Created on Nov 1, 2016

@author: nicolas
'''

import os.path as osp
import time

import pytest

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

from helpers.runner import run_suite_class, run_suite_classes, run_func_in_test
from helpers.report import assert_report_from_suite, assert_report_from_suites, get_last_test, get_last_attachment, \
    assert_attachment

SAMPLE_IMAGE_PATH = osp.join(osp.dirname(__file__), osp.pardir, "doc", "_static", "report-sample.png")

with open(SAMPLE_IMAGE_PATH, "rb") as fh:
    SAMPLE_IMAGE_CONTENT = fh.read()


def _get_suite(report, suite_path=None):
    return report.get_suite(suite_path) if suite_path else report.get_suites()[0]


def _get_suite_setup(report, suite_path=None):
    suite = _get_suite(report, suite_path)
    return suite.suite_setup


def _get_suite_teardown(report, suite_path=None):
    suite = _get_suite(report, suite_path)
    return suite.suite_teardown


def make_file_reader(binary=False):
    def reader(path):
        with open(path, "rb" if binary else "r") as fh:
            content = fh.read()
        return content
    return reader


def test_simple_test():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

    report = run_suite_class(mysuite)

    assert_report_from_suite(report, mysuite)


def test_test_with_all_metadata():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.link("http://foo.bar", "foobar")
        @lcc.prop("foo", "bar")
        @lcc.tags("foo", "bar")
        @lcc.test("Some test")
        def sometest(self):
            pass

    report = run_suite_class(mysuite)

    assert_report_from_suite(report, mysuite)


def test_suite_with_all_metadata():
    @lcc.link("http://foo.bar", "foobar")
    @lcc.prop("foo", "bar")
    @lcc.tags("foo", "bar")
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

    report = run_suite_class(mysuite)

    assert_report_from_suite(report, mysuite)


def test_multiple_suites_and_tests():
    @lcc.suite("MySuite1")
    class mysuite1:
        @lcc.tags("foo")
        @lcc.test("Some test 1")
        def test_1_1(self):
            pass

        @lcc.tags("bar")
        @lcc.test("Some test 2")
        def test_1_2(self):
            pass

        @lcc.tags("baz")
        @lcc.test("Some test 3")
        def test_1_3(self):
            pass

    @lcc.suite("MySuite2")
    class mysuite2:
        @lcc.prop("foo", "bar")
        @lcc.test("Some test 1")
        def test_2_1(self):
            pass

        @lcc.prop("foo", "baz")
        @lcc.test("Some test 2")
        def test_2_2(self):
            pass

        @lcc.test("Some test 3")
        def test_2_3(self):
            pass

        # suite3 is a sub suite of suite2
        @lcc.suite("MySuite3")
        class mysuite3:
            @lcc.prop("foo", "bar")
            @lcc.test("Some test 1")
            def test_3_1(self):
                pass

            @lcc.prop("foo", "baz")
            @lcc.test("Some test 2")
            def test_3_2(self):
                pass

            @lcc.test("Some test 3")
            def test_3_3(self):
                pass

    report = run_suite_classes([mysuite1, mysuite2])

    assert_report_from_suites(report, [mysuite1, mysuite2])


def test_check_success():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Test 1")
        def test_1(self):
            check_that("somevalue", "foo", equal_to("foo"))

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "passed"
    step = test.get_steps()[0]
    assert "somevalue" in step.get_logs()[0].description
    assert "foo" in step.get_logs()[0].description
    assert step.get_logs()[0].is_successful is True
    assert "foo" in step.get_logs()[0].details


def test_check_failure():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Test 1")
        def test_1(self):
            check_that("somevalue", "foo", equal_to("bar"))

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "failed"
    step = test.get_steps()[0]
    assert "somevalue" in step.get_logs()[0].description
    assert "bar" in step.get_logs()[0].description
    assert step.get_logs()[0].is_successful is False
    assert "foo" in step.get_logs()[0].details


def test_require_success():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Test 1")
        def test_1(self):
            require_that("somevalue", "foo", equal_to("foo"))

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "passed"
    step = test.get_steps()[0]
    assert "somevalue" in step.get_logs()[0].description
    assert "foo" in step.get_logs()[0].description
    assert step.get_logs()[0].is_successful is True
    assert "foo" in step.get_logs()[0].details


def test_require_failure():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Test 1")
        def test_1(self):
            require_that("somevalue", "foo", equal_to("bar"))

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "failed"
    step = test.get_steps()[0]
    assert "somevalue" in step.get_logs()[0].description
    assert "bar" in step.get_logs()[0].description
    assert step.get_logs()[0].is_successful is False
    assert "foo" in step.get_logs()[0].details


def test_all_types_of_logs():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.log_debug("some debug message")
            lcc.log_info("some info message")
            lcc.log_warning("some warning message")

        @lcc.test("Test 2")
        def test_2(self):
            lcc.log_error("some error message")

    report = run_suite_class(mysuite)

    test = report.get_test("mysuite.test_1")
    assert test.status == "passed"
    step = test.get_steps()[0]
    assert step.get_logs()[0].level == "debug"
    assert step.get_logs()[0].message == "some debug message"
    assert step.get_logs()[1].level == "info"
    assert step.get_logs()[1].message == "some info message"
    assert step.get_logs()[2].level == "warn"

    test = report.get_test("mysuite.test_2")
    assert test.status == "failed"
    step = test.get_steps()[0]
    assert step.get_logs()[0].message == "some error message"
    assert step.get_logs()[0].level == "error"


def test_multiple_steps():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.set_step("step 1")
            lcc.log_info("do something")
            lcc.set_step("step 2")
            lcc.log_info("do something else")

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "passed"
    steps = test.get_steps()
    assert steps[0].description == "step 1"
    assert steps[0].get_logs()[0].level == "info"
    assert steps[0].get_logs()[0].message == "do something"
    assert steps[1].description == "step 2"
    assert steps[1].get_logs()[0].level == "info"
    assert steps[1].get_logs()[0].message == "do something else"


def test_multiple_steps_on_different_threads():
    def thread_func(i):
        lcc.set_step(str(i))
        time.sleep(0.001)
        lcc.log_info(str(i))

    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            threads = [lcc.Thread(target=thread_func, args=(i,)) for i in range(3)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    remainings = list(range(3))

    steps = test.get_steps()
    for step in steps:
        remainings.remove(int(step.description))
        assert len(step.get_logs()) == 1
        assert step.get_logs()[0].message == step.description

    assert len(remainings) == 0


def test_thread_logging_without_explicit_step():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            thread = lcc.Thread(target=lambda: lcc.log_info("doing something"))
            thread.start()
            thread.join()

    report = run_suite_class(mysuite)

    test = get_last_test(report)

    assert test.status == "passed"
    assert len(test.get_steps()) == 1
    step = test.get_steps()[0]
    assert step.description == "Some test"
    assert step.get_logs()[0].level == "info"
    assert "doing something" == step.get_logs()[0].message


def test_thread_logging_without_detached_bis():
    def func():
        lcc.log_info("log in thread")

    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.set_step("Step 1")
            lcc.log_info("log 1")
            thread = lcc.Thread(target=func)
            lcc.set_step("Step 2")
            lcc.log_info("log 2")
            thread.start()
            thread.join()

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "passed"

    steps = test.get_steps()
    assert len(steps) == 3

    step = test.get_steps()[0]
    assert step.description == "Step 1"
    assert step.get_logs()[0].message == "log 1"

    step = test.get_steps()[1]
    assert step.description == "Step 2"
    assert step.get_logs()[0].message == "log 2"

    step = test.get_steps()[2]
    assert step.description == "Step 1"
    assert step.get_logs()[0].message == "log in thread"


def test_exception_in_thread():
    def thread_func():
        lcc.log_info("doing something")
        raise Exception("this_is_an_exception")

    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            thread = lcc.Thread(target=thread_func)
            thread.start()
            thread.join()

    report = run_suite_class(mysuite)

    test = get_last_test(report)

    assert test.status == "failed"
    steps = test.get_steps()
    assert len(steps) == 1
    step = steps[0]
    assert step.description == "Some test"
    assert step.get_logs()[-1].level == "error"
    assert "this_is_an_exception" in step.get_logs()[-1].message


def test_same_step_in_two_threads():
    def thread_func():
        lcc.set_step("step 2")
        lcc.log_info("log 2")
        time.sleep(0.001)
        lcc.set_step("step 1")
        lcc.log_info("log 3")

    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.set_step("step 1")
            lcc.log_info("log 1")
            thread = lcc.Thread(target=thread_func)
            thread.start()
            lcc.log_info("log 4")
            thread.join()

    report = run_suite_class(mysuite)

    test = get_last_test(report)

    steps = test.get_steps()
    assert len(steps) == 3

    step = steps[0]
    assert step.description == "step 1"
    assert len(step.get_logs()) == 2
    assert step.get_logs()[0].message == "log 1"
    assert step.get_logs()[1].message == "log 4"

    step = steps[1]
    assert step.description == "step 2"
    assert len(step.get_logs()) == 1
    assert step.get_logs()[0].message == "log 2"

    step = steps[2]
    assert step.description == "step 1"
    assert len(step.get_logs()) == 1
    assert step.get_logs()[0].message == "log 3"


def test_deprecated_end_step():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.set_step("step")
            lcc.log_info("log")
            lcc.end_step("step")

    with pytest.warns(DeprecationWarning, match="deprecated"):
        report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "passed"
    step = test.get_steps()[0]
    assert step.description == "step"
    assert step.get_logs()[0].level == "info"
    assert step.get_logs()[0].message == "log"


def test_deprecated_detached_step():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            with lcc.detached_step("step"):
                lcc.log_info("log")

    with pytest.warns(DeprecationWarning, match="deprecated"):
        report = run_suite_class(mysuite)

    test = get_last_test(report)
    step = test.get_steps()[0]
    assert test.status == "passed"
    assert step.description == "step"
    assert step.get_logs()[0].level == "info"
    assert step.get_logs()[0].message == "log"


def test_default_step():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.log_info("do something")

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "passed"
    step = test.get_steps()[0]
    assert step.description == "Some test"
    assert step.get_logs()[0].level == "info"
    assert step.get_logs()[0].message == "do something"


def test_step_after_test_setup():
    @lcc.suite("mysuite")
    class mysuite:
        def setup_test(self, test):
            lcc.log_info("in test setup")

        @lcc.test("Some test")
        def sometest(self):
            lcc.log_info("do something")

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "passed"
    steps = test.get_steps()
    assert steps[0].description == "Setup test"
    assert steps[0].get_logs()[0].level == "info"
    assert steps[0].get_logs()[0].message == "in test setup"
    assert steps[1].description == "Some test"
    assert steps[1].get_logs()[0].level == "info"
    assert steps[1].get_logs()[0].message == "do something"


def test_prepare_attachment(tmpdir):
    def do():
        with lcc.prepare_attachment("foobar.txt", "some description") as filename:
            with open(filename, "w") as fh:
                fh.write("some content")

    report = run_func_in_test(do, tmpdir=tmpdir)

    assert_attachment(
        get_last_attachment(report), "foobar.txt", "some description", False, "some content", make_file_reader()
    )


def test_prepare_image_attachment(tmpdir):
    def do():
        with lcc.prepare_image_attachment("foobar.png", "some description") as filename:
            with open(filename, "wb") as fh:
                fh.write(SAMPLE_IMAGE_CONTENT)

    report = run_func_in_test(do, tmpdir=tmpdir)

    assert_attachment(
        get_last_attachment(report), "foobar.png", "some description", True, SAMPLE_IMAGE_CONTENT,
        make_file_reader(binary=True)
    )


def test_save_attachment_file(tmpdir):
    def do():
        filename = osp.join(tmpdir.strpath, "somefile.txt")
        with open(filename, "w") as fh:
            fh.write("some other content")
        lcc.save_attachment_file(filename, "some other file")

    report = run_func_in_test(do, tmpdir=tmpdir.mkdir("report"))

    assert_attachment(
        get_last_attachment(report), "somefile.txt", "some other file", False, "some other content", make_file_reader()
    )


def test_save_image_file(tmpdir):
    def do():
        lcc.save_image_file(SAMPLE_IMAGE_PATH, "some other file")

    report = run_func_in_test(do, tmpdir=tmpdir.mkdir("report"))

    assert_attachment(
        get_last_attachment(report), osp.basename(SAMPLE_IMAGE_PATH), "some other file", True, SAMPLE_IMAGE_CONTENT,
        make_file_reader(binary=True)
    )


def _test_save_attachment_content(tmpdir, file_name, file_content, file_reader):
    def do():
        lcc.save_attachment_content(file_content, file_name)

    report = run_func_in_test(do, tmpdir=tmpdir)

    assert_attachment(get_last_attachment(report), file_name, file_name, False, file_content, file_reader)


def test_save_attachment_text_ascii(tmpdir):
    _test_save_attachment_content(tmpdir, "foobar.txt", "foobar", make_file_reader())


def test_save_attachment_text_utf8(tmpdir):
    _test_save_attachment_content(tmpdir, "foobar.txt", "éééçççààà", make_file_reader())


def test_save_attachment_binary(tmpdir):
    _test_save_attachment_content(tmpdir, "foobar.png", SAMPLE_IMAGE_CONTENT, make_file_reader(binary=True))


def test_save_image_content(tmpdir):
    def do():
        lcc.save_image_content(SAMPLE_IMAGE_CONTENT, "somefile.png", "some file")

    report = run_func_in_test(do, tmpdir=tmpdir)

    assert_attachment(
        get_last_attachment(report), "somefile.png", "some file", True, SAMPLE_IMAGE_CONTENT,
        make_file_reader(binary=True)
    )


def test_log_url():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.log_url("http://example.com", "example")

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    step = test.get_steps()[0]
    assert step.get_logs()[0].description == "example"
    assert step.get_logs()[0].url == "http://example.com"


def test_unicode(tmpdir):
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("some test")
        def sometest(self):
            lcc.set_step("éééààà")
            check_that("éééààà", 1, equal_to(1))
            lcc.log_info("éééààà")
            lcc.save_attachment_content("A" * 1024, "somefileààà", "éééààà")

    report = run_suite_class(mysuite, tmpdir=tmpdir)

    test = get_last_test(report)
    assert test.status == "passed"
    step = test.get_steps()[0]
    assert step.description == "éééààà"
    assert "éééààà" in step.get_logs()[0].description
    assert "1" in step.get_logs()[0].description
    assert step.get_logs()[1].message == "éééààà"
    assert_attachment(step.get_logs()[2], "somefileààà", "éééààà", False, "A" * 1024, make_file_reader())


def test_setup_suite_success():
    @lcc.suite("MySuite")
    class mysuite:
        def setup_suite(self):
            lcc.log_info("some log")

        @lcc.test("Some test")
        def sometest(self):
            pass

    report = run_suite_class(mysuite)

    setup = _get_suite_setup(report)
    assert setup.status == "passed"
    assert setup.start_time is not None
    assert setup.end_time is not None
    assert setup.get_steps()[0].get_logs()[0].message == "some log"
    assert setup.is_successful()


def test_setup_suite_failure():
    @lcc.suite("MySuite")
    class mysuite:
        def setup_suite(self):
            lcc.log_error("something bad happened")

        @lcc.test("Some test")
        def sometest(self):
            pass

    report = run_suite_class(mysuite)

    setup = _get_suite_setup(report)
    assert setup.status == "failed"
    assert setup.start_time is not None
    assert setup.end_time is not None
    assert setup.get_steps()[0].get_logs()[0].message == "something bad happened"
    assert not setup.is_successful()


def test_setup_suite_without_content():
    @lcc.suite("MySuite")
    class mysuite:
        def setup_suite(self):
            pass

        @lcc.test("Some test")
        def sometest(self):
            pass

    report = run_suite_class(mysuite)

    assert _get_suite_setup(report) is None


def test_teardown_suite_success():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            lcc.log_info("some log")

    report = run_suite_class(mysuite)

    teardown = _get_suite_teardown(report)
    assert teardown.status == "passed"
    assert teardown.start_time is not None
    assert teardown.end_time is not None
    assert teardown.get_steps()[0].get_logs()[0].message == "some log"
    assert teardown.is_successful()


def test_teardown_suite_failure():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            check_that("val", 1, equal_to(2))

    report = run_suite_class(mysuite)

    teardown = _get_suite_teardown(report)
    assert teardown.status == "failed"
    assert teardown.start_time is not None
    assert teardown.end_time is not None
    assert teardown.get_steps()[0].get_logs()[0].is_successful is False
    assert not teardown.is_successful()


def test_teardown_suite_without_content():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            pass

    report = run_suite_class(mysuite)

    assert _get_suite_teardown(report) is None


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

    setup = report.test_session_setup
    assert setup.status == "passed"
    assert setup.start_time is not None
    assert setup.end_time is not None
    assert setup.get_steps()[0].get_logs()[0].message == "some log"
    assert setup.is_successful()


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

    setup = report.test_session_setup
    assert setup.status == "failed"
    assert setup.start_time is not None
    assert setup.end_time is not None
    assert setup.get_steps()[0].get_logs()[0].message == "something bad happened"
    assert not setup.is_successful()


def test_setup_test_session_without_content():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    @lcc.fixture(scope="session")
    def fixt():
        pass

    report = run_suite_class(mysuite, fixtures=[fixt])

    assert report.test_session_setup is None


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

    teardown = report.test_session_teardown
    assert teardown.status == "passed"
    assert teardown.start_time is not None
    assert teardown.end_time is not None
    assert teardown.get_steps()[0].get_logs()[0].message == "some log"
    assert teardown.is_successful()


def test_teardown_test_session_failure():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    @lcc.fixture(scope="session")
    def fixt():
        yield
        check_that("val", 1, equal_to(2))

    report = run_suite_class(mysuite, fixtures=[fixt])

    teardown = report.test_session_teardown
    assert teardown.status == "failed"
    assert teardown.start_time is not None
    assert teardown.end_time is not None
    assert teardown.get_steps()[0].get_logs()[0].is_successful is False
    assert not teardown.is_successful()


def test_teardown_test_session_without_content():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    @lcc.fixture(scope="session")
    def fixt():
        yield

    report = run_suite_class(mysuite, fixtures=[fixt])

    assert report.test_session_teardown is None


def test_add_report_info():
    @lcc.suite("Some suite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.add_report_info("some info", "some data")

    report = run_suite_class(mysuite)

    assert report.info[-1] == ["some info", "some data"]
