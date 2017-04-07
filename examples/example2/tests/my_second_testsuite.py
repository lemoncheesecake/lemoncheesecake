import lemoncheesecake.api as lcc

@lcc.testsuite("My second testsuite")
class my_second_testsuite:
	@lcc.test("Some test")
	def some_other_test(self, project_dir):
		lcc.log_info("project dir: %s" % project_dir)
