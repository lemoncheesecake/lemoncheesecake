from lemoncheesecake import *

TESTSUITE = {
    "description": "B"
}

@testsuite("BB1")
class BB1:
    @test("Test of BB1")
    def c_test_1(self):
        import time
        time.sleep(1)
        assert_eq("value", 32, 54)

@testsuite("BB2")
class BB2:
    @test("Test of BB2")
    def d_test_1(self):
        save_attachment_content("blah " * 100, "sometext.txt", "Some text")
