import time

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *
from lemoncheesecake.matching.matcher import Matcher, MatchResult

MULTI_LINE_TEXT = "- first line\n- second line\n- third line"


class MultipleOf(Matcher):
    def __init__(self, value):
        self.value = value

    def build_description(self, transformation):
        return transformation("to be a multiple of %s" % self.value)

    def matches(self, actual):
        return MatchResult(actual % self.value == 0, "got %s" % actual)


def multiple_of(value):
    return MultipleOf(value)


@lcc.suite("A")
@lcc.tags("my_tag")
@lcc.prop("key1", "value1")
@lcc.prop("key2", "value2")
class A:
    description = "A Suite"
    
    def __init__(self):
        for i in range(4):
            def dummy():
                lcc.log_info("do test dyn %d" % i)
            lcc.add_test_into_suite(lcc.Test("test_%d" % i, "This is my dynamic test %d" % i, dummy), self)

    @lcc.tags("my_tag1")
    @lcc.test("My test description")
    def this_is_a_test(self, fixt1, fixt9):
        lcc.set_step("Test list matchers")
        check_that("my list", [1, 2], has_length(3))
        check_that("my other list", [1, 2, 3], has_items((1, 4)))
        check_that("param", ("foo", "baz"), has_items(("bar",)))
        check_that("param", "foo", is_in(("foo", "bar")))
        check_that("param", "baz", is_in(("foo", "bar")))

        lcc.set_step("Test dict matchers")
        check_that("dict", {"foo", 1}, has_entry("foo"))
        check_that("dict", {"foo", 1}, has_entry("foo", is_integer()))
        check_that("dict", {"foo", (1, 2)}, has_entry("foo", is_list()))
        check_that("dict", {"foo": {"foo": "bar"}}, has_entry("foo", is_dict()))
        check_that("dict", {"foo": 1}, has_entry("foo", equal_to(1)))

        lcc.set_step("Test simple value matchers")
        check_that("some value", 1, equal_to(1))
        check_that("some value", 1, equal_to(2))
        check_that("some string", "foo", equal_to("bar"))
        check_that("some integer", "1", is_integer(1))
        check_that("some boolean", True, is_bool(True))

    def foo(self):
        pass

    @lcc.prop("priority", "high")
    @lcc.link("http://bugtracker.net/tickets/1234")    
    @lcc.link("http://bugtracker.net/tickets/5678")
    @lcc.test("Second test")
    @lcc.disabled()
    def second_test(self):
        time.sleep(2)
        lcc.log_info("do test 2 !")
    
    def bar(self):
        pass
    
    @lcc.link("http://bugtracker.net/tickets/444", "#444")
    @lcc.test("Third test")
    def third_test(self):
        lcc.log_error("something goes wrong")
        #raise AbortSuite()
    
    @lcc.test("Fourth test")
    def fourth_test(self):
        pass

    @lcc.suite(MULTI_LINE_TEXT)
    class multi_line_description_suite:
        @lcc.test(MULTI_LINE_TEXT)
        def multi_line_description_test(self):
            lcc.set_step(MULTI_LINE_TEXT)
            lcc.log_info("some log")
    
    @lcc.suite("HTML Escaping")
    @lcc.tags("<h1>My Tag</h1>")    
    @lcc.prop("<h1>Prop name</h1>", "<h1>Prop value</h1>")
    @lcc.link("http://bugtracker.net/tickets/1234", "<h1>link name</h1>")    
    class HtmlEscaping:
        description = "<h1>Test suite</h1>"

        @lcc.tags("<h1>My Tag</h1>")    
        @lcc.prop("<h1>Prop name</h1>", "<h1>Prop value</h1>")
        @lcc.link("http://bugtracker.net/tickets/1234", "<h1>link name</h1>")    
        @lcc.test("<h1>html escaping</h1>")
        def html_escaping(self):
            lcc.set_step("<h1>step description</h1>")
            check_that("<h1>value</h1>", "<h1>actual</h1>", equal_to("<h1>expected</h1>"))
            lcc.log_info("<h1>some log</h1>")
            lcc.save_attachment_content("content", "filename", "<h1>attachment</h1>")
    
    @lcc.suite("A very loong suite")
    class a_very_lllllllllllllllllllllllooooooooooooooooooooooooooooooooonnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnggggggggggggggggggggggg_suite_name:
        @lcc.test("A test within a suite with a long name")
        def the_test_within_the_suite_with_long_name(self):
            lcc.set_step("lllllllllllllllllllllllllllllllooooooooooooooooooooooonnnnnnnnnnngggggggggggggggg step")
            time.sleep(3)
    
    @lcc.suite("a_suite_without_direct_tests")
    class a_suite_without_direct_tests:
        @lcc.suite("a_suite_with_parent_without_direct_tests")
        class a_suite_with_parent_without_direct_tests:
            @lcc.test("Yet Another Test")
            def yet_another_test(self):
                check_that("string", "foo", not_equal_to("foo"))
