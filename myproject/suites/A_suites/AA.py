from lemoncheesecake.testsuite import *
from lemoncheesecake.checkers import *

class AAA(TestSuite):
    @test("Test of AAA")
    def test_of_B(self):
        pass

@tickets("1234")
class AA(TestSuite):
    sub_testsuite_classes = [ AAA ]

    def before_suite(self):
        step("hep csdcnlns csdlcsdl cubsd ucds")
        info("some stuff in before suite")

    def after_suite(self):
        step("hopi csdknclsdc lsdclusbcl ubsd")
        info("some other stuff in after suite")

    @test("Test of A")
    def test_of_A(self):
        pass