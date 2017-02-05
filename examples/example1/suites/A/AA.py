from lemoncheesecake import *


@testsuite("AA")
@link("http://bugtracker.net/tickets/1234")
class AA:
    def setup_suite(self):
        set_step("hep csdcnlns csdlcsdl cubsd ucds")
        log_info("some stuff in before suite")

    def teardown_suite(self):
        set_step("hopi csdknclsdc lsdclusbcl ubsd")
        log_info("some other stuff in after suite")

    @test("Test of A")
    def test_of_A(self):
        raise AbortTest("this test cannot be executed")

    @testsuite("AAA")
    class AAA:
        @test("Test of AAA")
        def test_of_B(self):
            assert_eq("value", 1, 2)
