import re
import argparse

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *
# import _TestFilter as __TestFilter to avoid the class being interpreted as a test by pytest
from lemoncheesecake.filter import TestFilter as _TestFilter, ResultFilter, StepFilter, \
    add_result_filter_cli_args, add_test_filter_cli_args, add_step_filter_cli_args, \
    make_result_filter, make_test_filter, make_step_filter
from lemoncheesecake.suite import load_suites_from_classes, load_suite_from_class
from lemoncheesecake.testtree import flatten_tests, filter_suites
from lemoncheesecake.reporting.backends.json_ import JsonBackend
from lemoncheesecake.reporting import ReportLocation
from lemoncheesecake.reporting.reportdir import DEFAULT_REPORT_DIR_NAME
from lemoncheesecake.reporting.report import Log

from helpers.runner import run_suite, run_suites, run_suite_class, run_func_in_test
from helpers.report import make_report, make_suite_result, make_test_result, make_step
from helpers.utils import change_dir


def _test_filter(suites, filtr, expected_test_paths):
    filtered_suites = filter_suites(suites, filtr)
    filtered_tests = flatten_tests(filtered_suites)
    assert sorted(t.path for t in filtered_tests) == sorted(expected_test_paths)


def _test_test_filter(suite_classes, filtr, expected_test_paths):
    suites = load_suites_from_classes(suite_classes)
    _test_filter(suites, filtr, expected_test_paths)


def _test_result_filter(suites, filtr, expected, fixtures=None):
    if not isinstance(suites, (list, tuple)):
        suites = (suites,)

    report = run_suites(load_suites_from_classes(suites), fixtures=fixtures)
    results = list(filter(filtr, report.all_results()))

    assert len(results) == len(expected)
    for expected_result in expected:
        if isinstance(expected_result, str):
            expected_result = ReportLocation.in_test(expected_result)
        expected_result = report.get(expected_result)
        assert expected_result in results


def _test_step_filter(func, filtr, expected):
    report = run_func_in_test(func)
    steps = list(filter(filtr, report.all_steps()))

    assert [s.description for s in steps] == expected


def prepare_cli_args(args, func, **func_kwargs):
    cli_parser = argparse.ArgumentParser()
    func(cli_parser, **func_kwargs)
    return cli_parser.parse_args(args)


def test_filter_full_path_on_test():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(paths=["mysuite.subsuite.baz"]),
        ["mysuite.subsuite.baz"]
    )


def test_filter_simple_func():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        lambda test: test.path == "mysuite.subsuite.baz",
        ["mysuite.subsuite.baz"]
    )


def test_filter_full_path_on_test_negative():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(paths=["-mysuite.subsuite.baz"]),
        ["mysuite.subsuite.test2"]
    )


def test_filter_full_path_on_suite():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def test1(self):
                pass

            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(paths=["mysuite.subsuite"]),
        ["mysuite.subsuite.test1", "mysuite.subsuite.test2"]
    )


def test_filter_path_on_suite_negative():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(paths=["-mysuite.subsuite.*"]),
        []
    )


def test_filter_path_complete_on_top_suite():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def test1(self):
                pass

            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(paths=["mysuite"]),
        ["mysuite.subsuite.test1", "mysuite.subsuite.test2"]
    )


def test_filter_path_wildcard_on_test():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(paths=["mysuite.subsuite.ba*"]),
        ["mysuite.subsuite.baz"]
    )


def test_filter_path_wildcard_on_test_negative():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(paths=["-mysuite.subsuite.ba*"]),
        ["mysuite.subsuite.test2"]
    )


def test_filter_path_wildcard_on_suite():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(paths=["mysuite.sub*.baz"]),
        ["mysuite.subsuite.baz"]
    )


def test_filter_path_wildcard_on_suite_negative():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(paths=["~mysuite.sub*.baz"]),
        ["mysuite.subsuite.test2"]
    )


def test_filter_description_on_test():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("desc1")
            def baz(self):
                pass

            @lcc.test("desc2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(descriptions=[["desc2"]]),
        ["mysuite.subsuite.test2"]
    )


def test_filter_description_on_test_negative():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("desc1")
            def baz(self):
                pass

            @lcc.test("desc2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(descriptions=[["~desc2"]]),
        ["mysuite.subsuite.baz"]
    )


def test_filter_description_on_suite():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("desc1")
        class subsuite:
            @lcc.test("baz")
            def baz(self):
                pass

        @lcc.suite("desc2")
        class othersuite:
            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(descriptions=[["desc2"]]),
        ["mysuite.othersuite.test2"]
    )


def test_filter_description_on_suite_negative():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("desc1")
        class subsuite:

            @lcc.test("baz")
            def baz(self):
                pass

        @lcc.suite("desc2")
        class othersuite:

            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(descriptions=[["-desc2"]]),
        ["mysuite.subsuite.baz"]
    )


def test_filter_tag_on_test():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.tags("tag1")
            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(tags=[["tag1"]]),
        ["mysuite.subsuite.test2"]
    )


def test_filter_tag_on_test_negative():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.tags("tag1")
            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(tags=[["-tag1"]]),
        ["mysuite.subsuite.baz"]
    )


def test_filter_tag_on_suite():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.tags("tag1")
        @lcc.suite("subsuite1")
        class subsuite1:
            @lcc.test("test1")
            def baz(self):
                pass

        @lcc.tags("tag2")
        @lcc.suite("subsuite2")
        class subsuite2:
            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(tags=[["tag2"]]),
        ["mysuite.subsuite2.test2"]
    )


def test_filter_tag_on_suite_negative():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.tags("tag1")
        @lcc.suite("subsuite1")
        class subsuite1:
            @lcc.test("test1")
            def baz(self):
                pass

        @lcc.tags("tag2")
        @lcc.suite("subsuite2")
        class subsuite2:
            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(tags=[["~tag2"]]),
        ["mysuite.subsuite1.baz"]
    )


def test_filter_property_on_test():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.prop("myprop", "foo")
            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(properties=[[("myprop", "foo")]]),
        ["mysuite.subsuite.test2"]
    )


def test_filter_property_on_test_negative():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.prop("myprop", "bar")
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.prop("myprop", "foo")
            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(properties=[[("myprop", "-foo")]]),
        ["mysuite.subsuite.baz"]
    )


def test_filter_property_on_suite():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.prop("myprop", "foo")
        @lcc.suite("subsuite1")
        class subsuite1:
            @lcc.test("test1")
            def baz(self):
                pass

        @lcc.prop("myprop", "bar")
        @lcc.suite("subsuite2")
        class subsuite2:
            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(properties=[[("myprop", "bar")]]),
        ["mysuite.subsuite2.test2"]
    )


def test_filter_property_on_suite_negative():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.prop("myprop", "foo")
        @lcc.suite("subsuite1")
        class subsuite1:
            @lcc.test("test1")
            def baz(self):
                pass

        @lcc.prop("myprop", "bar")
        @lcc.suite("subsuite2")
        class subsuite2:
            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(properties=[[("myprop", "~bar")]]),
        ["mysuite.subsuite1.baz"]
    )


def test_filter_link_on_test_without_name():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.link("http://bug.trac.ker/1234")
            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(links=[["http://bug.trac.ker/1234"]]),
        ["mysuite.subsuite.test2"]
    )


def test_filter_link_on_test_negative_with_name():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.link("http://bug.trac.ker/1234", "#1234")
            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(links=[["-#1234"]]),
        ["mysuite.subsuite.baz"]
    )


def test_filter_link_on_suite():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.link("http://bug.trac.ker/1234", "#1234")
        @lcc.suite("subsuite1")
        class subsuite1:
            @lcc.test("test1")
            def baz(self):
                pass

        @lcc.link("http://bug.trac.ker/1235", "#1235")
        @lcc.suite("subsuite2")
        class subsuite2:
            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(links=[["#1235"]]),
        ["mysuite.subsuite2.test2"]
    )


def test_filter_link_on_suite_negative():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.link("http://bug.trac.ker/1234", "#1234")
        @lcc.suite("subsuite1")
        class subsuite1:
            @lcc.test("test1")
            def baz(self):
                pass

        @lcc.link("http://bug.trac.ker/1235", "#1235")
        @lcc.suite("subsuite2")
        class subsuite2:
            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(links=[["~#1235"]]),
        ["mysuite.subsuite1.baz"]
    )


def test_filter_path_on_suite_and_tag_on_test():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.tags("tag1")
            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(paths=["mysuite.subsuite"], tags=[["tag1"]]),
        ["mysuite.subsuite.test2"]
    )


def test_filter_path_on_suite_and_negative_tag_on_test():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.tags("tag1")
            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(paths=["mysuite.subsuite"], tags=[["-tag1"]]),
        ["mysuite.subsuite.baz"]
    )


def test_filter_description_on_suite_and_link_on_test():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def test1(self):
                pass

        @lcc.suite("Sub suite 2")
        class subsuite2:
            @lcc.link("http://my.bug.trac.ker/1234", "#1234")
            @lcc.test("test2")
            def test2(self):
                pass

            @lcc.test("test3")
            def test3(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(descriptions=[["Sub suite 2"]], links=[["#1234"]]),
        ["mysuite.subsuite2.test2"]
    )


def test_filter_path_and_tag_on_suite():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.tags("foo")
        @lcc.suite("subsuite1")
        class subsuite1:
            @lcc.test("test1")
            def test1(self):
                pass

        @lcc.tags("foo")
        @lcc.suite("subsuite2")
        class subsuite2:
            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(paths=["mysuite.subsuite1"], tags=[["foo"]]),
        ["mysuite.subsuite1.test1"]
    )


def test_filter_path_and_tag_on_test():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite1")
        class subsuite1:
            @lcc.tags("foo")
            @lcc.test("test1")
            def test1(self):
                pass

        @lcc.suite("subsuite2")
        class subsuite2:
            @lcc.tags("foo")
            @lcc.test("test2")
            def test2(self):
                pass

            @lcc.test("test3")
            def test3(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(paths=["mysuite.subsuite2.*"], tags=[["foo"]]),
        ["mysuite.subsuite2.test2"]
    )


def test_filter_path_and_negative_tag_on_test():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite1")
        class subsuite1:
            @lcc.tags("foo")
            @lcc.test("test1")
            def test1(self):
                pass

        @lcc.suite("subsuite2")
        class subsuite2:
            @lcc.tags("foo")
            @lcc.test("test2")
            def test2(self):
                pass

            @lcc.test("test3")
            def test3(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(paths=["mysuite.subsuite2.*"], tags=[["-foo"]]),
        ["mysuite.subsuite2.test3"]
    )


def test_filter_disabled():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.test("test1")
        def test1(self):
            pass

        @lcc.test("test2")
        @lcc.disabled()
        def test2(self):
            pass

    _test_test_filter(
        [mysuite],
        _TestFilter(disabled=True),
        ["mysuite.test2"]
    )


def test_filter_enabled():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.test("test1")
        def test1(self):
            pass

        @lcc.test("test2")
        @lcc.disabled()
        def test2(self):
            pass

    _test_test_filter(
        [mysuite],
        _TestFilter(enabled=True),
        ["mysuite.test1"]
    )


def test_empty_filter():
    filt = _TestFilter()
    assert not filt


def test_non_empty_filter():
    def do_test(attr, val):
        filtr = _TestFilter()
        assert hasattr(filtr, attr)
        setattr(filtr, attr, val)
        assert filtr

    do_test("paths", ["foo"])
    do_test("descriptions", [["foo"]])
    do_test("tags", [["foo"]])
    do_test("properties", [[("foo", "bar")]])
    do_test("links", ["foo"])


def test_filter_description_and():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            def baz(self):
                pass

            @lcc.test("test2")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(descriptions=[["mysuite"], ["test1"]]),
        ["mysuite.subsuite.baz"]
    )


def test_filter_tags_and():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            @lcc.tags("foo", "bar")
            def baz(self):
                pass

            @lcc.test("test2")
            @lcc.tags("foo")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(tags=[["foo"], ["bar"]]),
        ["mysuite.subsuite.baz"]
    )


def test_filter_properties_and():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            @lcc.prop("foo", "1")
            @lcc.prop("bar", "2")
            def baz(self):
                pass

            @lcc.test("test2")
            @lcc.prop("foo", "1")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(properties=[[("foo", "1")], [("bar", "2")]]),
        ["mysuite.subsuite.baz"]
    )


def test_filter_links_and():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            @lcc.link("http://a.b.c/1234", "#1234")
            @lcc.link("http://a.b.c/1235")
            def baz(self):
                pass

            @lcc.test("test2")
            @lcc.link("http://a.b.c/1234", "#1234")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(links=[["#1234"], ["*/1235"]]),
        ["mysuite.subsuite.baz"]
    )


def test_filter_and_or():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.suite("subsuite")
        class subsuite:
            @lcc.test("test1")
            @lcc.tags("foo", "bar")
            def baz(self):
                pass

            @lcc.test("test2")
            @lcc.tags("foo", "baz")
            def test2(self):
                pass

    _test_test_filter(
        [mysuite],
        _TestFilter(tags=[["foo"], ["bar", "baz"]]),
        ["mysuite.subsuite.baz", "mysuite.subsuite.test2"]
    )


def test_result_filter_on_path():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test1")
        def test1(self):
            pass

        @lcc.test("test2")
        def test2(self):
            pass

    _test_result_filter(
        suite,
        ResultFilter(paths=["suite.test2"]),
        ["suite.test2"]
    )


def test_result_filter_on_passed():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test1")
        def test1(self):
            lcc.log_error("error")

        @lcc.test("test2")
        def test2(self):
            pass

    _test_result_filter(
        suite,
        ResultFilter(statuses=["passed"]),
        ["suite.test2"]
    )


def test_result_filter_on_failed():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test1")
        def test1(self):
            lcc.log_error("error")

        @lcc.test("test2")
        def test2(self):
            pass

    _test_result_filter(
        suite,
        ResultFilter(statuses=["failed"]),
        ["suite.test1"]
    )


def test_result_filter_with_setup_teardown_on_passed():
    @lcc.fixture(scope="session")
    def fixt():
        lcc.log_info("session setup")
        yield
        lcc.log_info("session teardown")

    @lcc.suite("suite")
    class suite(object):
        def setup_suite(self):
            lcc.log_info("setup suite")

        def teardown_suite(self):
            lcc.log_info("teadown suite")

        @lcc.test("test1")
        def test1(self, fixt):
            pass

        @lcc.test("test2")
        @lcc.disabled()
        def test2(self):
            pass

    _test_result_filter(
        suite,
        ResultFilter(statuses=["passed"]),
        (
            ReportLocation.in_test_session_setup(),
            ReportLocation.in_suite_setup("suite"),
            "suite.test1",
            ReportLocation.in_suite_teardown("suite"),
            ReportLocation.in_test_session_teardown()
        ),
        fixtures=(fixt,)
    )


def test_result_filter_with_setup_teardown_on_disabled():
    @lcc.fixture(scope="session")
    def fixt():
        lcc.log_info("session setup")
        yield
        lcc.log_info("session teardown")

    @lcc.suite("suite")
    class suite(object):
        def setup_suite(self):
            lcc.log_info("setup suite")

        def teardown_suite(self):
            lcc.log_info("teadown suite")

        @lcc.test("test1")
        def test1(self, fixt):
            pass

        @lcc.test("test2")
        @lcc.disabled()
        def test2(self):
            pass

    _test_result_filter(
        suite,
        ResultFilter(disabled=True),
        (
            "suite.test2",
        ),
        fixtures=(fixt,)
    )


def test_result_filter_with_setup_teardown_on_enabled():
    @lcc.fixture(scope="session")
    def fixt():
        lcc.log_info("session setup")
        yield
        lcc.log_info("session teardown")

    @lcc.suite("suite")
    class suite(object):
        def setup_suite(self):
            lcc.log_info("setup suite")

        def teardown_suite(self):
            lcc.log_info("teadown suite")

        @lcc.test("test1")
        def test1(self, fixt):
            pass

        @lcc.test("test2")
        @lcc.disabled()
        def test2(self):
            pass

    _test_result_filter(
        suite,
        ResultFilter(enabled=True),
        (
            ReportLocation.in_test_session_setup(),
            ReportLocation.in_suite_setup("suite"),
            "suite.test1",
            ReportLocation.in_suite_teardown("suite"),
            ReportLocation.in_test_session_teardown()
        ),
        fixtures=(fixt,)
    )


def test_result_filter_with_setup_teardown_on_tags():
    @lcc.fixture(scope="session")
    def fixt():
        lcc.log_info("session setup")
        yield
        lcc.log_info("session teardown")

    @lcc.suite("suite")
    @lcc.tags("mytag")
    class suite(object):
        def setup_suite(self):
            lcc.log_info("setup suite")

        def teardown_suite(self):
            lcc.log_info("teadown suite")

        @lcc.test("test1")
        def test1(self, fixt):
            pass

        @lcc.test("test2")
        @lcc.disabled()
        def test2(self):
            pass

    _test_result_filter(
        suite,
        ResultFilter(tags=[["mytag"]]),
        (
            ReportLocation.in_suite_setup("suite"),
            "suite.test1",
            "suite.test2",
            ReportLocation.in_suite_teardown("suite")
        ),
        fixtures=(fixt,)
    )


def test_result_filter_with_setup_teardown_on_failed_and_skipped():
    @lcc.fixture(scope="session")
    def fixt():
        lcc.log_info("session setup")
        yield
        lcc.log_info("session teardown")

    @lcc.suite("suite")
    class suite(object):
        def setup_suite(self):
            lcc.log_error("some error")

        def teardown_suite(self):
            lcc.log_info("teadown suite")

        @lcc.test("test1")
        def test1(self, fixt):
            pass

        @lcc.test("test2")
        @lcc.disabled()
        def test2(self):
            pass

    _test_result_filter(
        suite,
        ResultFilter(statuses=("failed", "skipped")),
        (
            ReportLocation.in_suite_setup("suite"),
            "suite.test1"
        ),
        fixtures=(fixt,)
    )


def test_result_filter_with_setup_teardown_on_grep():
    @lcc.fixture(scope="session")
    def fixt():
        lcc.log_info("foobar")
        yield
        lcc.log_info("foobar")

    @lcc.suite("suite")
    class suite(object):
        def setup_suite(self):
            lcc.log_info("foobar")

        def teardown_suite(self):
            lcc.log_info("foobar")

        @lcc.test("test1")
        def test1(self, fixt):
            lcc.log_info("foobar")

    _test_result_filter(
        suite,
        ResultFilter(grep=re.compile(r"foobar")),
        (
            ReportLocation.in_test_session_setup(),
            ReportLocation.in_suite_setup("suite"),
            "suite.test1",
            ReportLocation.in_suite_teardown("suite"),
            ReportLocation.in_test_session_teardown()
        ),
        fixtures=(fixt,)
    )


def test_result_filter_grep_no_result():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.set_step("some step")
            lcc.log_info("something")
            lcc.log_check("check", True, "1")
            lcc.log_url("http://www.example.com")
            lcc.save_attachment_content("A" * 100, "file.txt")

    _test_result_filter(
        suite,
        ResultFilter(grep=re.compile(r"foobar")),
        expected=()
    )


def test_result_filter_grep_step():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.set_step("foobar")
            lcc.log_info("something")

    _test_result_filter(
        suite,
        ResultFilter(grep=re.compile(r"foobar")),
        expected=("suite.test",)
    )


def test_result_filter_grep_log():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.log_info("foobar")

    _test_result_filter(
        suite,
        ResultFilter(grep=re.compile(r"foobar")),
        expected=("suite.test",)
    )


def test_result_filter_grep_check_description():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.log_check("foobar", True)

    _test_result_filter(
        suite,
        ResultFilter(grep=re.compile(r"foobar")),
        expected=("suite.test",)
    )


def test_result_filter_grep_check_details():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.log_check("something", True, "foobar")

    _test_result_filter(
        suite,
        ResultFilter(grep=re.compile(r"foobar")),
        expected=("suite.test",)
    )


def test_result_filter_grep_url():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.log_url("http://example.com/foobar")

    _test_result_filter(
        suite,
        ResultFilter(grep=re.compile(r"foobar")),
        expected=("suite.test",)
    )


def test_result_filter_grep_attachment_filename():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.save_attachment_content("hello world", "foobar.txt")

    _test_result_filter(
        suite,
        ResultFilter(grep=re.compile(r"foobar")),
        expected=("suite.test",)
    )


def test_result_filter_grep_attachment_description():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.save_attachment_content("hello world", "file.txt", "foobar")

    _test_result_filter(
        suite,
        ResultFilter(grep=re.compile(r"foobar")),
        expected=("suite.test",)
    )


def test_result_filter_grep_url_description():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.log_url("http://example.com", "foobar")

    _test_result_filter(
        suite,
        ResultFilter(grep=re.compile(r"foobar")),
        expected=("suite.test",)
    )


def test_step_filter_no_criteria():
    def do():
        lcc.set_step("mystep")
        lcc.log_info("foobar")

    _test_step_filter(do, StepFilter(), ["mystep"])


def test_step_filter_passed_ok():
    def do():
        lcc.set_step("mystep")
        lcc.log_info("foobar")

    _test_step_filter(do, StepFilter(passed=True), ["mystep"])


def test_step_filter_passed_ko_because_of_log_error():
    def do():
        lcc.set_step("mystep")
        lcc.log_error("foobar")

    _test_step_filter(do, StepFilter(passed=True), [])


def test_step_filter_passed_ko_because_of_check_error():
    def do():
        lcc.set_step("mystep")
        check_that("value", 1, equal_to(2))

    _test_step_filter(do, StepFilter(passed=True), [])


def test_step_filter_failed_ok():
    def do():
        lcc.set_step("mystep")
        lcc.log_error("foobar")

    _test_step_filter(do, StepFilter(failed=True), ["mystep"])


def test_step_filter_failed_ko():
    def do():
        lcc.set_step("mystep")
        lcc.log_info("foobar")

    _test_step_filter(do, StepFilter(failed=True), [])


def test_step_filter_grep_ok():
    def do():
        lcc.set_step("mystep")
        lcc.log_error("foobar")

    _test_step_filter(do, StepFilter(grep=re.compile("foo")), ["mystep"])


def test_step_filter_grep_ko():
    def do():
        lcc.set_step("mystep")
        lcc.log_info("foobar")

    _test_step_filter(do, StepFilter(grep=re.compile("baz")), [])


def test_step_filter_through_parent_ok():
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.set_step("mystep")
            lcc.log_info("foobar")

    report = run_suite_class(suite)

    steps = list(filter(StepFilter(paths=("suite.test",)), report.all_steps()))

    assert [s.description for s in steps] == ["mystep"]


def test_step_filter_in_suite_setup():
    @lcc.suite("suite")
    class suite:
        def setup_suite(self):
            lcc.set_step("setup_suite")
            lcc.log_info("in setup_suite")

        @lcc.test("test")
        def test(self):
            lcc.set_step("mystep")
            lcc.log_info("foobar")

    report = run_suite_class(suite)

    steps = list(filter(StepFilter(grep=re.compile("in setup_suite")), report.all_steps()))

    assert [s.description for s in steps] == ["setup_suite"]


def test_step_filter_in_session_setup():
    @lcc.fixture(scope="session")
    def fixt():
        lcc.set_step("setup_session")
        lcc.log_info("in setup_session")

    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self, fixt):
            lcc.set_step("mystep")
            lcc.log_info("foobar")

    report = run_suite_class(suite, fixtures=(fixt,))

    steps = list(filter(StepFilter(grep=re.compile("in setup_session")), report.all_steps()))

    assert [s.description for s in steps] == ["setup_session"]


def test_step_filter_through_parent_ko():
    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        def test(self):
            lcc.set_step("mystep")
            lcc.log_info("foobar")

    report = run_suite_class(suite)

    steps = list(filter(StepFilter(paths=("unknown.test",)), report.all_steps()))

    assert len(steps) == 0


def test_filter_suites_on_suite_setup():
    @lcc.suite("suite")
    class suite(object):
        def setup_suite(self):
            lcc.log_info("foobar")

        @lcc.test("test")
        def test(self):
            pass

    report = run_suite_class(suite)

    suites = list(filter_suites(report.get_suites(), ResultFilter(grep=re.compile("foobar"))))

    assert len(suites) == 1


def test_filter_suites_on_suite_teardown():
    @lcc.suite("suite")
    class suite(object):
        def teardown_suite(self):
            lcc.log_info("foobar")

        @lcc.test("test")
        def test(self):
            pass

    report = run_suite_class(suite)

    suites = list(filter_suites(report.get_suites(), ResultFilter(grep=re.compile("foobar"))))

    assert len(suites) == 1


def test_make_test_filter():
    filtr = make_test_filter(prepare_cli_args([], add_test_filter_cli_args))
    assert not filtr


def test_make_test_filter_from_report(tmpdir):
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.test("mytest")
        def mytest(self):
            pass

    suite = load_suite_from_class(mysuite)

    run_suite(suite, backends=[JsonBackend()], tmpdir=tmpdir)

    cli_args = prepare_cli_args(["--from-report", tmpdir.strpath], add_test_filter_cli_args)
    filtr = make_test_filter(cli_args)
    assert filtr(suite.get_tests()[0])


def test_make_test_filter_from_report_implicit(tmpdir):
    def do_test(args, expected):
        filtr = make_test_filter(prepare_cli_args(args, add_test_filter_cli_args))
        assert filtr._tests == expected

    report = make_report(
        suites=[
            make_suite_result(
                name="tests",
                tests=(
                    make_test_result(name="passed", status="passed"),
                    make_test_result(name="failed", status="failed"),
                    make_test_result(name="skipped", status="skipped"),
                    make_test_result(
                        name="grepable", status="passed",
                        steps=[
                            make_step(logs=[Log(Log.LEVEL_INFO, "this is grepable", ts=0)])
                        ]
                    )
                )
            )
        ]
    )
    backend = JsonBackend()
    tmpdir.mkdir(DEFAULT_REPORT_DIR_NAME)
    backend.save_report(tmpdir.join(DEFAULT_REPORT_DIR_NAME, "report.json").strpath, report)
    with change_dir(tmpdir.strpath):
        do_test(["--passed"], ["tests.passed", "tests.grepable"])
        do_test(["--failed"], ["tests.failed"])
        do_test(["--skipped"], ["tests.skipped"])
        do_test(["--grep", "grepable"], ["tests.grepable"])
        do_test(["--non-passed"], ["tests.failed", "tests.skipped"])


def test_make_result_filter():
    filtr = make_result_filter(prepare_cli_args([], add_result_filter_cli_args))
    assert not filtr


def test_add_result_filter_cli_args():
    cli_args = prepare_cli_args([], add_result_filter_cli_args)
    assert hasattr(cli_args, "passed")
    assert hasattr(cli_args, "failed")
    assert hasattr(cli_args, "skipped")
    assert hasattr(cli_args, "enabled")
    assert hasattr(cli_args, "disabled")
    assert hasattr(cli_args, "non_passed")
    assert hasattr(cli_args, "grep")


def test_add_result_filter_cli_args_with_only_executed_tests():
    cli_args = prepare_cli_args([], add_result_filter_cli_args, only_executed_tests=True)
    assert hasattr(cli_args, "passed")
    assert hasattr(cli_args, "failed")
    assert not hasattr(cli_args, "skipped")
    assert not hasattr(cli_args, "enabled")
    assert not hasattr(cli_args, "disabled")
    assert not hasattr(cli_args, "non_passed")
    assert hasattr(cli_args, "grep")


def test_add_step_filter_cli_args():
    cli_args = prepare_cli_args([], add_step_filter_cli_args)
    assert hasattr(cli_args, "passed")
    assert hasattr(cli_args, "failed")
    assert not hasattr(cli_args, "skipped")
    assert not hasattr(cli_args, "enabled")
    assert not hasattr(cli_args, "disabled")
    assert not hasattr(cli_args, "non_passed")
    assert hasattr(cli_args, "grep")


def test_make_result_filter_with_only_executed_tests():
    cli_args = prepare_cli_args([], add_result_filter_cli_args, only_executed_tests=True)
    filtr = make_result_filter(cli_args, only_executed_tests=True)
    assert filtr.statuses == {"passed", "failed"}


def test_make_result_filter_with_only_executed_tests_and_passed():
    cli_args = prepare_cli_args(["--passed"], add_result_filter_cli_args, only_executed_tests=True)
    filtr = make_result_filter(cli_args, only_executed_tests=True)
    assert filtr.statuses == {"passed"}


def test_make_result_filter_non_passed():
    cli_args = prepare_cli_args(["--non-passed"], add_result_filter_cli_args)
    filtr = make_result_filter(cli_args)
    assert filtr.statuses == {"skipped", "failed"}


def test_make_result_filter_grep():
    cli_args = prepare_cli_args(["--grep", "foobar"], add_result_filter_cli_args)
    filtr = make_result_filter(cli_args)
    assert filtr.grep


def test_make_step_filter_passed():
    cli_args = prepare_cli_args(["--passed"], add_step_filter_cli_args)
    filtr = make_step_filter(cli_args)
    assert filtr.passed
