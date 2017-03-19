#!/usr/bin/python

import urllib
import urllib2
import json

from lemoncheesecake.testsuite import import_testsuites_from_directory
import lemoncheesecake as lcc

class OmdbAPI:
    def __init__(self, host):
        self.host = host
        lcc.log_info("Initialize OmdbAPI to %s" % self.host)
    
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

@lcc.fixture(scope="session")
def omdb(cli_args):
    return OmdbAPI(cli_args.host)

def add_cli_args(cli_parser):
    cli_parser.add_argument("--host", default="www.omdbapi.com", help="omdb API host")
CLI_EXTRA_ARGS = add_cli_args

TESTSUITES = import_testsuites_from_directory("tests")
FIXTURES = [omdb]
