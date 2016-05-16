from lemoncheesecake.testsuite import *
from lemoncheesecake.checkers import *

class A(TestSuite):
    description = "A Suite"
    
    @tags("my_tag1")
    @test("My test description")
    def this_is_a_test(self):
        step("test list checkers")
        info("do test 1 !")
        check_list_len("my list", [1,2], 3)
        check_list_contains("my other list", [ 1, 2, 3 ], [ 1, 4])
        step("test dict checkers")
        check_dict_has_key("my dict", { "foo": 33 }, "fool")
        check_dict_value2("bar", { "bar": 33 }, { "bar": 33 }, check_eq)
        check_dict_value2_with_default("bar", { "bar": 33 }, { "ball": 11 }, check_eq, default=33)
        step("test simple value checkers")
        info("something else")
        check_eq("some value", 1, 1)
        check_eq("some value", 1, 2)
        check_str_eq("some string", "foo", "bar")
        check_int_eq("my num", "33", 33)
        step("test dict composed checkers")
        check_dict_value_str_eq("foo", {"foo": "bar"}, "bar")
        check_pattern("some value", "foo bar", re.compile("foo.+"))
        check_str_does_not_match_pattern("some value", "foo bar", re.compile("foo.+"))
        
    def foo(self):
        pass

    @tickets("1234")    
    @test("Second test")
    def second_test(self):
        info("do test 2 !")
    
    def bar(self):
        pass
    
    @test("Third test")
    def third_test(self):
        error("something goes wrong")
        #raise AbortTestSuite()
    
    def load_generated_tests(self):
        tests = []
        for i in range(4):
            def dummy(suite):
                info("do test dyn %d" % i)
            tests.append(Test("test_%d" % i, "This is my dynamic test %d" % i, dummy))
        self.register_tests(tests, after_test="this_is_a_test")