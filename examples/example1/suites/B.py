from lemoncheesecake import *

@suite_rank(1)
class B(TestSuite):
    class BB1(TestSuite):
        @test("Test of BB1")
        def c_test_1(self):
            import time
            time.sleep(1)
            assert_eq("value", 32, 54)
    
    class BB2(TestSuite):
        @test("Test of BB2")
        def d_test_1(self):
            save_attachment_content("blah " * 100, "sometext.txt", "Some text")
