import re
import argparse

import lemoncheesecake.api as lcc
from lemoncheesecake.filter import RunFilter, ReportFilter, \
    add_report_filter_cli_args, add_run_filter_cli_args, make_report_filter, make_run_filter
from lemoncheesecake.suite import load_suites_from_classes, load_suite_from_class
from lemoncheesecake.testtree import flatten_tests, filter_suites
from lemoncheesecake.reporting.backends.json_ import JsonBackend
from lemoncheesecake.reporting import ReportLocation

from helpers.testtreemockup import suite_mockup, tst_mockup, make_suite_data_from_mockup
from helpers.runner import run_suite, run_suites, run_suite_class


def _test_filter(suites, filtr, expected_test_paths):
    filtered_suites = filter_suites(suites, filtr)
    filtered_tests = flatten_tests(filtered_suites)
    assert sorted(t.path for t in filtered_tests) == sorted(expected_test_paths)


def _test_run_filter(suite_classes, filtr, expected_test_paths):
    suites = load_suites_from_classes(suite_classes)
    _test_filter(suites, filtr, expected_test_paths)


def _test_report_filter(suites, filtr, expected, fixtures=None):
    if not isinstance(suites, (list, tuple)):
        suites = (suites,)

    report = run_suites(load_suites_from_classes(suites), fixtures=fixtures)
    results = list(report.all_results(filtr))

    assert len(results) == len(expected)
    for expected_result in expected:
        if isinstance(expected_result, str):
            expected_result = ReportLocation.in_test(expected_result)
        expected_result = report.get(expected_result)
        assert expected_result in results


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

    _test_run_filter(
        [mysuite],
        RunFilter(paths=["mysuite.subsuite.baz"]),
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

    _test_run_filter(
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

    _test_run_filter(
        [mysuite],
        RunFilter(paths=["-mysuite.subsuite.baz"]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(paths=["mysuite.subsuite"]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(paths=["-mysuite.subsuite.*"]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(paths=["mysuite"]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(paths=["mysuite.subsuite.ba*"]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(paths=["-mysuite.subsuite.ba*"]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(paths=["mysuite.sub*.baz"]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(paths=["~mysuite.sub*.baz"]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(descriptions=[["desc2"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(descriptions=[["~desc2"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(descriptions=[["desc2"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(descriptions=[["-desc2"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(tags=[["tag1"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(tags=[["-tag1"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(tags=[["tag2"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(tags=[["~tag2"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(properties=[[("myprop", "foo")]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(properties=[[("myprop", "-foo")]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(properties=[[("myprop", "bar")]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(properties=[[("myprop", "~bar")]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(links=[["http://bug.trac.ker/1234"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(links=[["-#1234"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(links=[["#1235"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(links=[["~#1235"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(paths=["mysuite.subsuite"], tags=[["tag1"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(paths=["mysuite.subsuite"], tags=[["-tag1"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(descriptions=[["Sub suite 2"]], links=[["#1234"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(paths=["mysuite.subsuite1"], tags=[["foo"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(paths=["mysuite.subsuite2.*"], tags=[["foo"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(paths=["mysuite.subsuite2.*"], tags=[["-foo"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(disabled=True),
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

    _test_run_filter(
        [mysuite],
        RunFilter(enabled=True),
        ["mysuite.test1"]
    )


def test_empty_filter():
    filt = RunFilter()
    assert not filt


def test_non_empty_filter():
    def do_test(attr, val):
        filtr = RunFilter()
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

    _test_run_filter(
        [mysuite],
        RunFilter(descriptions=[["mysuite"], ["test1"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(tags=[["foo"], ["bar"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(properties=[[("foo", "1")], [("bar", "2")]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(links=[["#1234"], ["*/1235"]]),
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

    _test_run_filter(
        [mysuite],
        RunFilter(tags=[["foo"], ["bar", "baz"]]),
        ["mysuite.subsuite.baz", "mysuite.subsuite.test2"]
    )


def test_report_filter_on_path():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test1")
        def test1(self):
            pass

        @lcc.test("test2")
        def test2(self):
            pass

    _test_report_filter(
        suite,
        ReportFilter(paths=["suite.test2"]),
        ["suite.test2"]
    )


def test_report_filter_on_passed():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test1")
        def test1(self):
            lcc.log_error("error")

        @lcc.test("test2")
        def test2(self):
            pass

    _test_report_filter(
        suite,
        ReportFilter(statuses=["passed"]),
        ["suite.test2"]
    )


def test_report_filter_on_failed():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test1")
        def test1(self):
            lcc.log_error("error")

        @lcc.test("test2")
        def test2(self):
            pass

    _test_report_filter(
        suite,
        ReportFilter(statuses=["failed"]),
        ["suite.test1"]
    )


def test_report_filter_with_setup_teardown_on_passed():
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

    _test_report_filter(
        suite,
        ReportFilter(statuses=["passed"]),
        (
            ReportLocation.in_test_session_setup(),
            ReportLocation.in_suite_setup("suite"),
            "suite.test1",
            ReportLocation.in_suite_teardown("suite"),
            ReportLocation.in_test_session_teardown()
        ),
        fixtures=(fixt,)
    )


def test_report_filter_with_setup_teardown_on_disabled():
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

    _test_report_filter(
        suite,
        ReportFilter(disabled=True),
        (
            "suite.test2",
        ),
        fixtures=(fixt,)
    )


def test_report_filter_with_setup_teardown_on_enabled():
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

    _test_report_filter(
        suite,
        ReportFilter(enabled=True),
        (
            ReportLocation.in_test_session_setup(),
            ReportLocation.in_suite_setup("suite"),
            "suite.test1",
            ReportLocation.in_suite_teardown("suite"),
            ReportLocation.in_test_session_teardown()
        ),
        fixtures=(fixt,)
    )


def test_report_filter_with_setup_teardown_on_tags():
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

    _test_report_filter(
        suite,
        ReportFilter(tags=[["mytag"]]),
        (
            ReportLocation.in_suite_setup("suite"),
            "suite.test1",
            "suite.test2",
            ReportLocation.in_suite_teardown("suite")
        ),
        fixtures=(fixt,)
    )


def test_report_filter_with_setup_teardown_on_failed_and_skipped():
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

    _test_report_filter(
        suite,
        ReportFilter(statuses=("failed", "skipped")),
        (
            ReportLocation.in_suite_setup("suite"),
            "suite.test1"
        ),
        fixtures=(fixt,)
    )


def test_report_filter_with_setup_teardown_on_grep():
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

    _test_report_filter(
        suite,
        ReportFilter(grep=re.compile(r"foobar")),
        (
            ReportLocation.in_test_session_setup(),
            ReportLocation.in_suite_setup("suite"),
            "suite.test1",
            ReportLocation.in_suite_teardown("suite"),
            ReportLocation.in_test_session_teardown()
        ),
        fixtures=(fixt,)
    )


def test_report_filter_grep_no_result():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.set_step("some step")
            lcc.log_info("something")
            lcc.log_check("check", True, "1")
            lcc.log_url("http://www.example.com")
            lcc.save_attachment_content("A" * 100, "file.txt")

    _test_report_filter(
        suite,
        ReportFilter(grep=re.compile(r"foobar")),
        expected=()
    )


def test_report_filter_grep_step():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.set_step("foobar")
            lcc.log_info("something")

    _test_report_filter(
        suite,
        ReportFilter(grep=re.compile(r"foobar")),
        expected=("suite.test",)
    )


def test_report_filter_grep_log():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.log_info("foobar")

    _test_report_filter(
        suite,
        ReportFilter(grep=re.compile(r"foobar")),
        expected=("suite.test",)
    )


def test_report_filter_grep_check_description():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.log_check("foobar", True)

    _test_report_filter(
        suite,
        ReportFilter(grep=re.compile(r"foobar")),
        expected=("suite.test",)
    )


def test_report_filter_grep_check_details():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.log_check("something", True, "foobar")

    _test_report_filter(
        suite,
        ReportFilter(grep=re.compile(r"foobar")),
        expected=("suite.test",)
    )


def test_report_filter_grep_url():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.log_url("http://example.com/foobar")

    _test_report_filter(
        suite,
        ReportFilter(grep=re.compile(r"foobar")),
        expected=("suite.test",)
    )


def test_report_filter_grep_attachment_filename():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.save_attachment_content("hello world", "foobar.txt")

    _test_report_filter(
        suite,
        ReportFilter(grep=re.compile(r"foobar")),
        expected=("suite.test",)
    )


def test_report_filter_grep_attachment_description():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.save_attachment_content("hello world", "file.txt", "foobar")

    _test_report_filter(
        suite,
        ReportFilter(grep=re.compile(r"foobar")),
        expected=("suite.test",)
    )


def test_report_filter_grep_url_description():
    @lcc.suite("suite")
    class suite(object):
        @lcc.test("test")
        def test(self):
            lcc.log_url("http://example.com", "foobar")

    _test_report_filter(
        suite,
        ReportFilter(grep=re.compile(r"foobar")),
        expected=("suite.test",)
    )


def test_filter_suites_on_suite_setup():
    @lcc.suite("suite")
    class suite(object):
        def setup_suite(self):
            lcc.log_info("foobar")

        @lcc.test("test")
        def test(self):
            pass

    report = run_suite_class(suite)

    suites = list(report.all_suites(ReportFilter(grep=re.compile("foobar"))))

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

    suites = list(report.all_suites(ReportFilter(grep=re.compile("foobar"))))

    assert len(suites) == 1


def test_make_run_filter():
    cli_parser = argparse.ArgumentParser()
    add_run_filter_cli_args(cli_parser)
    cli_args = cli_parser.parse_args(args=[])
    filtr = make_run_filter(cli_args)
    assert not filtr


def test_run_filter_from_report(tmpdir):
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.test("mytest")
        def mytest(self):
            pass

    suite = load_suite_from_class(mysuite)

    run_suite(suite, backends=[JsonBackend()], tmpdir=tmpdir)

    cli_parser = argparse.ArgumentParser()
    add_run_filter_cli_args(cli_parser)
    cli_args = cli_parser.parse_args(args=["--from-report", tmpdir.strpath])
    filtr = make_report_filter(cli_args)
    assert filtr(suite.get_tests()[0])


def test_make_report_filter():
    cli_parser = argparse.ArgumentParser()
    add_report_filter_cli_args(cli_parser)
    cli_args = cli_parser.parse_args(args=[])
    filtr = make_report_filter(cli_args)
    assert not filtr


def test_add_report_filter_cli_args():
    cli_parser = argparse.ArgumentParser()
    add_report_filter_cli_args(cli_parser)
    cli_args = cli_parser.parse_args(args=[])
    assert hasattr(cli_args, "passed")
    assert hasattr(cli_args, "failed")
    assert hasattr(cli_args, "skipped")
    assert hasattr(cli_args, "enabled")
    assert hasattr(cli_args, "disabled")
    assert hasattr(cli_args, "non_passed")
    assert hasattr(cli_args, "grep")


def test_add_report_filter_cli_args_with_only_executed_tests():
    cli_parser = argparse.ArgumentParser()
    add_report_filter_cli_args(cli_parser, only_executed_tests=True)
    cli_args = cli_parser.parse_args(args=[])
    assert hasattr(cli_args, "passed")
    assert hasattr(cli_args, "failed")
    assert not hasattr(cli_args, "skipped")
    assert not hasattr(cli_args, "enabled")
    assert not hasattr(cli_args, "disabled")
    assert not hasattr(cli_args, "non_passed")
    assert hasattr(cli_args, "grep")


def test_make_report_filter_with_only_executed_tests():
    cli_parser = argparse.ArgumentParser()
    add_report_filter_cli_args(cli_parser, only_executed_tests=True)
    cli_args = cli_parser.parse_args(args=[])
    filtr = make_report_filter(cli_args, only_executed_tests=True)
    assert filtr.statuses == {"passed", "failed"}


def test_make_report_filter_with_only_executed_tests_and_passed():
    cli_parser = argparse.ArgumentParser()
    add_report_filter_cli_args(cli_parser, only_executed_tests=True)
    cli_args = cli_parser.parse_args(args=["--passed"])
    filtr = make_report_filter(cli_args, only_executed_tests=True)
    assert filtr.statuses == {"passed"}


def test_make_report_filter_non_passed():
    cli_parser = argparse.ArgumentParser()
    add_report_filter_cli_args(cli_parser)
    cli_args = cli_parser.parse_args(args=["--non-passed"])
    filtr = make_report_filter(cli_args)
    assert filtr.statuses == {"skipped", "failed"}


def test_make_report_filter_grep():
    cli_parser = argparse.ArgumentParser()
    add_report_filter_cli_args(cli_parser)
    cli_args = cli_parser.parse_args(args=["--grep", "foobar"])
    filtr = make_report_filter(cli_args)
    assert filtr.grep
