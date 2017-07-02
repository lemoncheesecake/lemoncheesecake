import lemoncheesecake.api as lcc

@lcc.suite("AA")
@lcc.link("http://bugtracker.net/tickets/1234")
class AA:
    def setup_suite(self):
        lcc.set_step("hep csdcnlns csdlcsdl cubsd ucds")
        lcc.log_info("some stuff in before suite")

    def teardown_suite(self):
        lcc.set_step("hopi csdknclsdc lsdclusbcl ubsd")
        lcc.log_info("some other stuff in after suite")

    @lcc.test("Test of A")
    def test_of_A(self):
        raise lcc.AbortTest("this test cannot be executed")

    @lcc.suite("AAA")
    class AAA:
        @lcc.test("Test of AAA")
        def test_of_B(self):
            lcc.assert_eq("value", 1, 2)
