from __future__ import print_function

import re
import sys

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *
from lemoncheesecake.reporting.console import Renderer

from helpers.runner import run_suite_classes, wrap_func_into_suites


def _test_render_test(suites, *expected_lines):
    report = run_suite_classes(suites)
    actual = "\n".join(Renderer(80).render_report(report))
    print("<<<\n%s\n>>>" % actual, file=sys.stderr)
    for actual_line, expected_line in zip(actual.split("\n"), expected_lines):
        assert re.compile(expected_line).search(actual_line)


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
        "CHECK.+foo",
        ""
    )


def test_log_checks_failure():
    def func():
        check_that("value", "bar", equal_to("foo"))
        lcc.log_error("something")

    _test_render_test(
        wrap_func_into_suites(func),
        r"Some test",
        r"MySuite.sometest",
        r"",
        r"Some test",
        r"",
        "CHECK.+foo.+bar",
        ""
    )


# TODO: improve this test suite to cover more test cases
