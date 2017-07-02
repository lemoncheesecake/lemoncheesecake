import lemoncheesecake.api as lcc

@lcc.suite("Suite 1")
class suite_1:
    @lcc.test("Test 1")
    @lcc.prop("priority", "low")
    @lcc.tags("slow")
    def test_1(self, fixt_1):
        pass

    @lcc.test("Test 2")
    @lcc.prop("priority", "low")
    def test_2(self, fixt_4):
        pass

    @lcc.test("Test 3")
    @lcc.prop("priority", "medium")
    @lcc.link("http://example.com/1235", "#1235")
    def test_3(self):
        pass

    @lcc.test("Test 4")
    @lcc.prop("priority", "low")
    def test_4(self, fixt_6):
        pass

    @lcc.test("Test 5")
    @lcc.prop("priority", "high")
    def test_5(self):
        pass

    @lcc.test("Test 6")
    @lcc.prop("priority", "high")
    @lcc.tags("slow")
    def test_6(self):
        pass

    @lcc.test("Test 7")
    @lcc.prop("priority", "high")
    def test_7(self, fixt_8):
        pass

    @lcc.test("Test 8")
    @lcc.prop("priority", "medium")
    def test_8(self):
        pass

    @lcc.test("Test 9")
    @lcc.prop("priority", "medium")
    def test_9(self):
        pass
