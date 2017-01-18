from lemoncheesecake import *

class my_second_testsuite(TestSuite):
	@test("Some test")
	def some_other_test(self, project_dir):
		log_info("project dir: %s" % project_dir)
