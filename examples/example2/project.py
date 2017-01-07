#!/usr/bin/python

import urllib
import urllib2
import json

from lemoncheesecake import loader
from lemoncheesecake import worker
import lemoncheesecake as lcc

class OmdbapiWorker(worker.Worker):
    def __init__(self):
        self.host = "www.omdbapi.com"
    
    def get_movie_info(self, movie, year):
        lcc.set_step("Make HTTP request")
        url = "http://{host}/?t={movie}&y={year}&plot=short&r=json".format(
            host=self.host, movie=urllib.quote(movie), year=int(year)
        )
        lcc.log_info("GET %s" % url)
        req = urllib2.urlopen(url)
        lcc.assert_eq("HTTP status code", req.code, 200)
         
        content = req.read()
        lcc.log_info("Response body: %s" % content)
        try:
            return json.loads(content)
        except ValueError:
            raise lcc.AbortTest("The returned JSON is not valid")

# launcher = Launcher()
# launcher.add_worker("omdb", OmdbapiWorker())
# for backend in get_available_backends():
#     launcher.add_reporting_backend(backend)
# launcher.load_testsuites(import_testsuites_from_directory("tests"))
# launcher.handle_cli()

WORKERS = {"omdb": OmdbapiWorker()}
TESTSUITES = loader.import_testsuites_from_directory("tests")