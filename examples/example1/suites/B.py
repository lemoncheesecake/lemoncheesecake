import lemoncheesecake.api as lcc

TESTSUITE = {
    "description": "B"
}

@lcc.testsuite("BB1")
class BB1:
    @lcc.test("Test of BB1")
    def c_test_1(self):
        import time
        time.sleep(1)
        lcc.assert_eq("value", 32, 54)

@lcc.testsuite("BB2")
class BB2:
    @lcc.test("Test of BB2")
    def d_test_1(self):
        lcc.save_attachment_content("blah " * 100, "sometext.txt", "Some text")
