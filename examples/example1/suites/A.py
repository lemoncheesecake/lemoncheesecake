from lemoncheesecake import *
import re

@suite_rank(2)
@tags("my_tag")
@prop("key1", "value1")
@prop("key2", "value2")
class A(TestSuite):
    description = "A Suite"
    
    @tags("my_tag1")
    @test("My test description")
    def this_is_a_test(self):
        set_step("test list checkers")
        log_info("do test 1 !")
        check_list_len("my list", [1,2], 3)
        check_list_contains("my other list", [ 1, 2, 3 ], [ 1, 4])
        set_step("test dict checkers")
        check_dict_has_key("foo", { "foo": 33 })
        check_dict_value("bar", { "bar": 33 }, { "bar": 33 }, check_eq)
        set_step("test simple value checkers")
        log_info("something else")
        check_eq("some value", 1, 1)
        check_eq("some value", 1, 2)
        check_str_eq("some string", "foo", "bar")
        check_int_eq("my num", "33", 33)
        set_step("test dict composed checkers")
        check_dictval_str_eq("foo", {"foo": "bar"}, "bar")
        check_str_match("some value", "foo bar", re.compile("foo.+"))
        check_str_does_not_match("some value", "foo bar", re.compile("foo.+"))
        
    def foo(self):
        pass

    @prop("priority", "high")
    @link("http://bugtracker.net/tickets/1234")    
    @link("http://bugtracker.net/tickets/5678")
    @test("Second test")
    def second_test(self):
        log_info("do test 2 !")
    
    def bar(self):
        pass
    
    @link("http://bugtracker.net/tickets/444", "#444")
    @test("Third test")
    def third_test(self):
        log_error("something goes wrong")
        #raise AbortTestSuite()
    
    @test("Fourth test")
    def fourth_test(self):
        check_gteq("value", 4, 2)
        check_str_contains("string", "foobar", "foo")
    
    def load_generated_tests(self):
        tests = []
        for i in range(4):
            def dummy(suite):
                log_info("do test dyn %d" % i)
            tests.append(Test("test_%d" % i, "This is my dynamic test %d" % i, dummy))
        self.register_tests(tests, after_test="this_is_a_test")
