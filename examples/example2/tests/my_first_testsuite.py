import re
import urllib2
import json

from lemoncheesecake import *

class my_first_testsuite(TestSuite):
	@test("Some test")
	def some_test(self):
# 		set_step("Make HTTP request")
# 		req = urllib2.urlopen("http://www.omdbapi.com/?t=matrix&y=1999&plot=short&r=json")
# 		assert_eq("HTTP status code", req.code, 200)
# 	 	
# 		set_step("Check JSON response")
# 		content = req.read()
# 		log_info("Raw JSON: %s" % content)
# 		try:
# 			data = json.loads(content)
# 		except ValueError:
# 			raise AbortTest("The returned JSON is not valid")
		data = worker.get_movie_info("matrix", 1999)
		set_step("Check movie information")
		check_dictval_str_eq("Title", data, "The Matrix")
		check_dictval_str_contains("Actors", data, "Keanu Reeves")
		check_dictval_str_match("Director", data, re.compile(".+Wachow?ski", re.I))
		if check_dict_has_key("imdbRating", data):
			check_gt("imdbRating", float(data["imdbRating"]), 8.5)