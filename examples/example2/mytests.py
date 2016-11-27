#!/usr/bin/python

import urllib
import urllib2
import json

from lemoncheesecake.launcher import Launcher, import_testsuites_from_directory
from lemoncheesecake.workers import Worker, add_worker
from lemoncheesecake import *

class OmdbapiWorker(Worker):
    def __init__(self):
        self.host = "www.omdbapi.com"
    
    def get_movie_info(self, movie, year):
        set_step("Make HTTP request")
        url = "http://{host}/?t={movie}&y={year}&plot=short&r=json".format(
            host=self.host, movie=urllib.quote(movie), year=int(year)
        )
        log_info("GET %s" % url)
        req = urllib2.urlopen(url)
        assert_eq("HTTP status code", req.code, 200)
         
        content = req.read()
        log_info("Response body: %s" % content)
        try:
            return json.loads(content)
        except ValueError:
            raise AbortTest("The returned JSON is not valid")

add_worker("omdb", OmdbapiWorker())

launcher = Launcher()
launcher.load_testsuites(import_testsuites_from_directory("tests"))
launcher.handle_cli()