import lemoncheesecake.api as lcc
from helpers import run_suite_class, reporting_session
from lemoncheesecake.filter import Filter, ReportFilter, filter_suites
from lemoncheesecake.suite import load_suite_from_class


def test_filter_full_path_on_test(reporting_session):
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

    filter = Filter()
    filter.paths.append("mysuite.subsuite.baz")

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_full_path_on_test_negative(reporting_session):
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

    filter = Filter()
    filter.paths.append("-mysuite.subsuite.baz")

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_full_path_on_suite(reporting_session):
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

    filter = Filter()
    filter.paths.append("mysuite.subsuite")

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 2

def test_filter_path_on_suite_negative(reporting_session):
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

    filter = Filter()
    filter.paths.append("-mysuite.subsuite.*")

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 0

def test_filter_path_complete_on_top_suite(reporting_session):
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

    filter = Filter()
    filter.paths.append("mysuite")

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 2

def test_filter_path_wildcard_on_test(reporting_session):
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

    filter = Filter()
    filter.paths.append("mysuite.subsuite.ba*")

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_path_wildcard_on_test_negative(reporting_session):
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

    filter = Filter()
    filter.paths.append("-mysuite.subsuite.ba*")

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_path_wildcard_on_suite(reporting_session):
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

    filter = Filter()
    filter.paths.append("mysuite.sub*.baz")

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_path_wildcard_on_suite_negative(reporting_session):
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

    filter = Filter()
    filter.paths.append("~mysuite.sub*.baz")

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_description_on_test(reporting_session):
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

    filter = Filter()
    filter.descriptions.append(["desc2"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_description_on_test_negative(reporting_session):
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

    filter = Filter()
    filter.descriptions.append(["~desc2"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_description_on_suite(reporting_session):
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

    filter = Filter()
    filter.descriptions.append(["desc2"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_description_on_suite_negative(reporting_session):
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

    filter = Filter()
    filter.descriptions.append(["-desc2"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_tag_on_test(reporting_session):
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

    filter = Filter()
    filter.tags.append(["tag1"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_tag_on_test_negative(reporting_session):
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

    filter = Filter()
    filter.tags.append(["-tag1"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_tag_on_suite(reporting_session):
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

    filter = Filter()
    filter.tags.append(["tag2"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_tag_on_suite_negative(reporting_session):
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

    filter = Filter()
    filter.tags.append(["~tag2"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_property_on_test(reporting_session):
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

    filter = Filter()
    filter.properties.append([("myprop", "foo")])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_property_on_test_negative(reporting_session):
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

    filter = Filter()
    filter.properties.append([("myprop", "-foo")])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_property_on_suite(reporting_session):
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

    filter = Filter()
    filter.properties.append([("myprop", "bar")])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_property_on_suite_negative(reporting_session):
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

    filter = Filter()
    filter.properties.append([("myprop", "~bar")])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_link_on_test_without_name(reporting_session):
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

    filter = Filter()
    filter.links.append(["http://bug.trac.ker/1234"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_link_on_test_negative_with_name(reporting_session):
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

    filter = Filter()
    filter.links.append(["-#1234"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_link_on_suite(reporting_session):
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

    filter = Filter()
    filter.links.append(["#1235"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_link_on_suite_negative(reporting_session):
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

    filter = Filter()
    filter.links.append(["~#1235"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_path_on_suite_and_tag_on_test(reporting_session):
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

    filter = Filter()
    filter.paths.append("mysuite.subsuite")
    filter.tags.append(["tag1"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_path_on_suite_and_negative_tag_on_test(reporting_session):
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

    filter = Filter()
    filter.paths.append("mysuite.subsuite")
    filter.tags.append(["-tag1"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_description_on_suite_and_link_on_test(reporting_session):
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

    filter = Filter()
    filter.descriptions.append(["Sub suite 2"])
    filter.links.append(["#1234"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_path_and_tag_on_suite(reporting_session):
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

    filter = Filter()
    filter.paths.append("mysuite.subsuite1")
    filter.tags.append(["foo"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test1"

def test_filter_path_and_tag_on_test(reporting_session):
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

    filter = Filter()
    filter.paths.append("mysuite.subsuite2.*")
    filter.tags.append(["foo"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test2"

def test_filter_path_and_negative_tag_on_test(reporting_session):
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

    filter = Filter()
    filter.paths.append("mysuite.subsuite2.*")
    filter.tags.append(["-foo"])

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "test3"

def test_is_empty_true():
    filt = Filter()
    assert filt.is_empty() == True

def test_is_empty_false():
    def do_test(attr, val):
        filt = Filter()
        assert hasattr(filt, attr)
        setattr(filt, attr, val)
        assert filt.is_empty() == False

    do_test("paths", ["foo"])
    do_test("descriptions", [["foo"]])
    do_test("tags", [["foo"]])
    do_test("properties", [[("foo", "bar")]])
    do_test("links", ["foo"])

def test_filter_description_and(reporting_session):
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

    filter = Filter()
    filter.descriptions = [["mysuite"], ["test1"]]

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_tags_and(reporting_session):
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

    filter = Filter()
    filter.tags = [["foo"], ["bar"]]

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_properties_and(reporting_session):
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

    filter = Filter()
    filter.properties = [[("foo", "1")], [("bar", "2")]]

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_links_and(reporting_session):
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

    filter = Filter()
    filter.links = [["#1234"], ["*/1235"]]

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 1
    assert reporting_session.last_test == "baz"

def test_filter_and_or(reporting_session):
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

    filter = Filter()
    filter.tags = [["foo"], ["bar", "baz"]]

    run_suite_class(mysuite, filter=filter)

    assert reporting_session.test_nb == 2


def test_project_filter():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.test("test 1")
        def test1(self):
            pass

        @lcc.test("test 2")
        def test2(self):
            pass

    report = run_suite_class(mysuite)

    filter = Filter()
    filter.paths.append("mysuite.test2")

    suites = filter_suites(report.get_suites(), filter)

    assert len(suites[0].get_tests()) == 1
    assert suites[0].get_tests()[0].name == "test2"


def test_project_filter_on_passed():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.test("test 1")
        def test1(self):
            lcc.log_error("fail")

        @lcc.test("test 2")
        def test2(self):
            pass

    report = run_suite_class(mysuite)

    filter = ReportFilter()
    filter.statuses.append("passed")

    suites = filter_suites(report.get_suites(), filter)

    assert len(suites[0].get_tests()) == 1
    assert suites[0].get_tests()[0].name == "test2"


def test_project_filter_on_failed():
    @lcc.suite("mysuite")
    class mysuite:
        @lcc.test("test 1")
        def test1(self):
            lcc.log_error("fail")

        @lcc.test("test 2")
        def test2(self):
            pass

    report = run_suite_class(mysuite)

    filter = ReportFilter()
    filter.statuses.append("failed")

    suites = filter_suites(report.get_suites(), filter)

    assert len(suites[0].get_tests()) == 1
    assert suites[0].get_tests()[0].name == "test1"
