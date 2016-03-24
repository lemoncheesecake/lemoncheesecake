from lemoncheesecake.testsuite import *
from lemoncheesecake.messages import info, error

class B(TestSuite):
    @test("Test of B")
    def test_of_B(self):
        pass

class A(TestSuite):
    sub_testsuite_classes = [ B ]
    
    @test("Test of A")
    def test_of_A(self):
        pass

class MyTestSuite(TestSuite):
    description = "This is a my test suite"
    sub_testsuite_classes = [ A ]
    
    @test("My test description")
    def this_is_a_test(self):
        info("do test 1 !")
    
    def foo(self):
        pass
    
    @test("Second test")
    def second_test(self):
        info("do test 2 !")
    
    def bar(self):
        pass
    
    @test("Third test")
    def third_test(self):
        error("something goes wrong")
        raise AbortTestSuite()
    
    def load_dynamic_tests(self):
        for i in range(4):
            def dummy(suite):
                info("do test dyn %d" % i)
            self.register_test("test_%d" % i, "This is my dynamic test %d" % i, dummy, after_test="this_is_a_test")

class MyTestSuite1(TestSuite):
    class C(TestSuite):
        @test("C test 1")
        def c_test_1(self):
            pass
    
    class D(TestSuite):
        @test("D test 1")
        def d_test_1(self):
            pass
    
    sub_testsuite_classes = [C, D]
        
if __name__ == "__main__":
    suite = MyTestSuite()
    suite.load()
    
    print "Suite id: %s" % suite.id
    print "Suite description: %s" % suite.description
    
    print "Tests:"
    for test in suite.get_tests():
        print "* %s" % test
        print test.callback
        print
    
    print "Test results"
    for test in suite.get_tests():
        test.callback(suite)