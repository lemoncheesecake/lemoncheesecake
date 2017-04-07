import re
import lemoncheesecake.api as lcc

@lcc.testsuite("My second testsuite")
class my_first_testsuite:
	@lcc.test("Some test")
	def some_test(self, omdb):
		data = omdb.get_movie_info("matrix", 1999)
		lcc.set_step("Check movie information")
		lcc.check_dictval_str_eq("Title", data, "The Matrix")
		lcc.check_dictval_str_contains("Actors", data, "Keanu Reeves")
		lcc.check_dictval_str_match("Director", data, re.compile(".+Wachow?ski", re.I))
		if lcc.check_dict_has_key("imdbRating", data):
			lcc.check_gt("imdbRating", float(data["imdbRating"]), 8.5)
