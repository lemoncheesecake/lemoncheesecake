from __future__ import print_function

import re
import sys

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *
from lemoncheesecake.reporting.console import Renderer

from helpers.runner import run_suite_classes, wrap_func_into_suites


def _test_render_test(suites, *expected_lines, **kwargs):
    report = run_suite_classes(suites)
    renderer = Renderer(kwargs.get("max_width", 80), kwargs.get("explicit", False))
    actual = "\n".join(renderer.render_results(report.all_results()))
    print("<<<\n%s\n>>>" % actual, file=sys.stderr)
    for actual_line, expected_line in zip(actual.split("\n"), expected_lines):
        assert re.compile(expected_line).search(actual_line), "Cannot find '%s'" % expected_line


def test_log_info():
    def func():
        lcc.log_info("something")

    _test_render_test(
        wrap_func_into_suites(func),
        r"Some test",
        r"MySuite.sometest",
        r"",
        r"Some test",
        r"",
        "INFO.+something",
        ""
    )


def test_log_error():
    def func():
        lcc.log_error("something")

    _test_render_test(
        wrap_func_into_suites(func),
        r"Some test",
        r"MySuite.sometest",
        r"",
        r"Some test",
        r"",
        "ERROR.+something",
        ""
    )


def test_url():
    def func():
        lcc.log_url("http://www.example.com", "A link")

    _test_render_test(
        wrap_func_into_suites(func),
        r"Some test",
        r"MySuite.sometest",
        r"",
        r"Some test",
        r"",
        r"URL.+http://www.example.com \(A link\)",
        r""
    )


def test_attachment():
    def func():
        lcc.save_attachment_content("data", "data.txt", "My file")

    _test_render_test(
        wrap_func_into_suites(func),
        r"Some test",
        r"MySuite.sometest",
        r"",
        r"Some test",
        r"",
        r"ATTACH.+My file.+data\.txt",
        r""
    )


def test_log_checks_success():
    def func():
        check_that("value", "foo", equal_to("foo"))
        lcc.log_error("something")

    _test_render_test(
        wrap_func_into_suites(func),
        r"Some test",
        r"MySuite.sometest",
        r"",
        r"Some test",
        r"",
        r"CHECK.+foo",
        r""
    )


def test_log_checks_failure():
    def func():
        check_that("value", "bar", equal_to("foo"))

    _test_render_test(
        wrap_func_into_suites(func),
        r"Some test",
        r"MySuite.sometest",
        r"",
        r"Some test",
        r"",
        r"CHECK.+foo.+bar",
        r""
    )


def test_explicit():
    def func():
        check_that("value1", "foo", equal_to("foo"))
        check_that("value2", "bar", equal_to("foo"))

    _test_render_test(
        wrap_func_into_suites(func),
        r"FAILED: Some test",
        r"MySuite.sometest",
        r"",
        r"Some test",
        r"",
        r"CHECK OK.+value1.+foo.+foo",
        r"",
        r"CHECK KO.+value2.+foo.+bar",
        r"",
        explicit=True
    )


def test_metadata():
    @lcc.suite("My Suite")
    @lcc.tags("tag1")
    @lcc.prop("prop1", "value1")
    @lcc.link("http://link1", "link_name1")
    class suite(object):
        @lcc.test("My Test")
        @lcc.tags("tag2")
        @lcc.prop("prop2", "value2")
        @lcc.link("http://link2")
        def test(self):
            pass

    _test_render_test(
        [suite],
        r"My Test",
        r"suite.test.+tag1.+tag2.+prop1:value1.+prop2:value2.+link_name1.+http://link2",
        r""
    )


# TODO: add test cases for test session / suite - setup / teardown
