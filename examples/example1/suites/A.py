import lemoncheesecake.api as lcc
import re
import time

@lcc.suite("A")
@lcc.tags("my_tag")
@lcc.prop("key1", "value1")
@lcc.prop("key2", "value2")
class A:
    description = "A Suite"
    
    def __init__(self):
        tests = []
        for i in range(4):
            def dummy(suite):
                lcc.log_info("do test dyn %d" % i)
            tests.append(lcc.Test("test_%d" % i, "This is my dynamic test %d" % i, dummy))
        lcc.add_tests_in_suite(tests, self, after_test="this_is_a_test")
    
    @lcc.tags("my_tag1")
    @lcc.test("My test description")
    def this_is_a_test(self, fixt1, fixt9):
        lcc.set_step("test list checkers")
        lcc.log_info("do test 1 !")
        lcc.check_list_len("my list", [1,2], 3)
        lcc.check_list_contains("my other list", [ 1, 2, 3 ], [ 1, 4])
        lcc.check_list_contains("param", ("foo", "baz"), ("bar", ))
        lcc.check_choice("param", "foo", ("foo", "bar"))
        lcc.check_choice("param", "baz", ("foo", "bar"))
        lcc.set_step("test dict checkers")
        lcc.check_dict_has_key("foo", { "foo": 33 })
        lcc.check_dict_has_int("foo", { "foo": 33 })
        lcc.check_dict_has_list("foo", { "foo": [1, 2] })
        lcc.check_dict_has_dict("foo", { "foo": {"foo": "bar"} })
        lcc.check_dict_value("bar", { "bar": 33 }, 33, lcc.check_eq, key_label="bar key")
        lcc.set_step("test simple value checkers")
        lcc.log_info("something else")
        lcc.check_eq("some value", 1, 1)
        lcc.check_eq("some value", 1, 2)
        lcc.check_str_eq("some string", "foo", "bar")
        lcc.check_int_eq("my num", "33", 33)
        lcc.set_step("test dict composed checkers")
        lcc.check_dictval_str_eq("foo", {"foo": "bar"}, "bar")
        lcc.check_str_match("some value", "foo bar", re.compile("foo.+"))
        lcc.check_str_does_not_match("some value", "foo bar", re.compile("foo.+"))
        lcc.check_int_eq("some value", None, None)
        lcc.check_dictval_int_eq("foo", {"foo": None}, None)
        lcc.check_int_eq("some value", 42, None)
        lcc.check_bool_eq("some bool", False, False)
        lcc.log_url("http://example.com")
        
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
        lcc.check_gteq("value", 4, 2)
        lcc.check_str_contains("string", "foobar", "foo")
    
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
            lcc.check_eq("<h1>value</h1>", "<h1>actual</h1>", "<h1>expected</h1>")
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
                lcc.check_str_not_eq("string", "foo", "foo")
        
