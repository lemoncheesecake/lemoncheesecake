import sys
import os.path as osp
import re
import xml.etree.ElementTree as ET

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

from lemoncheesecake.reporting.backends.junit import JunitBackend

from helpers.runner import run_suite_class


def get_junit_xml_from_suite(suite, tmpdir, stop_on_failure=False):
    junit_backend = JunitBackend()
    run_suite_class(suite, backends=[junit_backend], tmpdir=tmpdir, stop_on_failure=stop_on_failure)
    
    junit_xml_filename = osp.join(tmpdir.strpath, junit_backend.get_report_filename())
    
    with open(junit_xml_filename, "r") as fh:
        junit_xml_content = fh.read()
        print("Junit XML:", file=sys.stderr)
        print(junit_xml_content, file=sys.stderr)
        return ET.fromstring(junit_xml_content)


def assert_duration_format(value):
    assert re.compile(r"^\d.\d{3}").match(value)


def assert_timestamp_format(value):
    assert re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$").match(value)


def assert_testsuites(junit_xml, tests, failures=0):
    testsuites = junit_xml
    assert testsuites.attrib["tests"] == str(tests)
    assert testsuites.attrib["failures"] == str(failures)
    assert_duration_format(testsuites.attrib["time"])


def assert_testsuite(junit_xml, name, tests, failures=0, skipped=0):
    testsuite = junit_xml.find("testsuite[@name='%s']" % name)
    assert testsuite.attrib["tests"] == str(tests)
    assert testsuite.attrib["failures"] == str(failures)
    assert testsuite.attrib["skipped"] == str(skipped)
    assert_timestamp_format(testsuite.attrib["timestamp"])
    assert_duration_format(testsuite.attrib["time"])


def assert_testcase(junit_xml, name, steps_with_error=[], steps_with_failed_check=[], skipped=False):
    test = junit_xml.find("testsuite/testcase[@name='%s']" % name)
    assert_duration_format(test.attrib["time"])
    
    for msg in steps_with_failed_check:
        assert test.find("failure[@message=\"failed check in step %s\"]" % msg) is not None
    assert len(test.findall("failure")) == len(steps_with_failed_check)
    
    for msg in steps_with_error:
        assert test.find("error[@message=\"error log in step %s\"]" % msg) is not None
    assert len(test.findall("error")) == len(steps_with_error)
    
    assert len(test.findall("skipped")) == (1 if skipped else 0)


def test_success(tmpdir):
    @lcc.suite("Suite")
    class suite():
        @lcc.test("Test")
        def test(self):
            check_that("value", 1, is_(1))

    junit_xml = get_junit_xml_from_suite(suite, tmpdir)
    assert_testsuites(junit_xml, tests=1, failures=0)
    assert_testsuite(junit_xml, "suite", tests=1)
    assert_testcase(junit_xml, "test")


def test_error_log(tmpdir):
    @lcc.suite("Suite")
    class suite():
        @lcc.test("Test")
        def test(self):
            lcc.set_step("first step")
            lcc.log_info("info !")
            lcc.set_step("second step")
            lcc.log_error("error !")

    junit_xml = get_junit_xml_from_suite(suite, tmpdir)
    assert_testsuites(junit_xml, tests=0, failures=1)
    assert_testsuite(junit_xml, "suite", tests=1, failures=1)
    assert_testcase(junit_xml, "test", steps_with_error=["'second step': error !"])


def test_failed_check(tmpdir):
    @lcc.suite("Suite")
    class suite():
        @lcc.test("Test")
        def test(self):
            lcc.set_step("first step")
            check_that("value", 2, is_(1))

    junit_xml = get_junit_xml_from_suite(suite, tmpdir)
    assert_testsuites(junit_xml, tests=0, failures=1)
    assert_testsuite(junit_xml, "suite", tests=1, failures=1)
    assert_testcase(junit_xml, "test", steps_with_failed_check=["'first step', Expect value to be equal to 1: Got 2"])


def test_skipped_test(tmpdir):
    @lcc.suite("Suite")
    class suite():
        @lcc.test("Test 1")
        def test_1(self):
            lcc.set_step("first step")
            check_that("value", 2, is_(1))

        @lcc.test("Test 2")
        def test_2(self):
            pass

    junit_xml = get_junit_xml_from_suite(suite, tmpdir, stop_on_failure=True)
    assert_testsuites(junit_xml, tests=0, failures=1)
    assert_testsuite(junit_xml, "suite", tests=2, failures=1, skipped=1)
    assert_testcase(junit_xml, "test_1", steps_with_failed_check=["'first step', Expect value to be equal to 1: Got 2"])
    assert_testcase(junit_xml, "test_2", skipped=True)
