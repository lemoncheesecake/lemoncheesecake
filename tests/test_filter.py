import argparse

import lemoncheesecake.api as lcc
from lemoncheesecake.filter import RunFilter, ReportFilter, filter_suites, \
    add_report_filter_cli_args, add_run_filter_cli_args, make_report_filter, make_run_filter
from lemoncheesecake.suite import load_suites_from_classes, load_suite_from_class
from lemoncheesecake.testtree import flatten_tests
from lemoncheesecake.reporting.backends.json_ import JsonBackend

from helpers.testtreemockup import suite_mockup, tst_mockup, make_suite_data_from_mockup
from helpers.runner import run_suite


def _test_filter(suites, filtr, expected_test_paths):
    filtered_suites = filter_suites(suites, filtr)
    filtered_tests = flatten_tests(filtered_suites)
    assert sorted([t.path for t in filtered_tests]) == sorted(expected_test_paths)


def _test_run_filter(suite_classes, filtr, expected_test_paths):
    suites = load_suites_from_classes(suite_classes)
    _test_filter(suites, filtr, expected_test_paths)


def _test_report_filter(suite_mockups, filtr, expected_test_paths):
    suites = map(make_suite_data_from_mockup, suite_mockups)
    _test_filter(suites, filtr, expected_test_paths)


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
    suite = suite_mockup("mysuite").add_test(tst_mockup("mytest1")).add_test(tst_mockup("mytest2"))

    _test_report_filter(
        [suite],
        ReportFilter(paths=["mysuite.mytest2"]),
        ["mysuite.mytest2"]
    )


def test_report_filter_on_passed():
    suite = suite_mockup("mysuite").\
        add_test(tst_mockup("test1", status="failed")).\
        add_test(tst_mockup("test2", status="passed"))

    _test_report_filter(
        [suite],
        ReportFilter(statuses=["passed"]),
        ["mysuite.test2"]
    )


def test_project_filter_on_failed():
    suite = suite_mockup("mysuite").\
        add_test(tst_mockup("test1", status="failed")).\
        add_test(tst_mockup("test2", status="passed"))

    _test_report_filter(
        [suite],
        ReportFilter(statuses=["failed"]),
        ["mysuite.test1"]
    )


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
