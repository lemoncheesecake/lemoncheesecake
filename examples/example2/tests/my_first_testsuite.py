import re

from lemoncheesecake import *

class my_first_testsuite(TestSuite):
	@test("Some test")
	def some_test(self):
		data = worker.get_movie_info("matrix", 1999)
		set_step("Check movie information")
		check_dictval_str_eq("Title", data, "The Matrix")
		check_dictval_str_contains("Actors", data, "Keanu Reeves")
		check_dictval_str_match("Director", data, re.compile(".+Wachow?ski", re.I))
		if check_dict_has_key("imdbRating", data):
			check_gt("imdbRating", float(data["imdbRating"]), 8.5)
