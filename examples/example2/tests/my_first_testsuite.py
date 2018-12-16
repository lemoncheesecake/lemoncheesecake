import re
import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *


@lcc.suite("My first suite", rank=1)
class my_first_testsuite:
	@lcc.test("Some test")
	def some_test(self, omdb):
		data = omdb.get_movie_info("matrix", 1999)
		lcc.set_step("Check movie information")
		check_that_in(
			data,
			"Title", "The Matrix",
			"Actors", contains_string("Keanu Reeves"),
			"Director", re.compile(".+Wachow?ski", re.I),
			"imdbRating", is_float(8.5)
		)
