#!/usr/bin/python

import os.path as osp
import urllib
import urllib2
import json

from lemoncheesecake.project import Project
from lemoncheesecake.fixtures import load_fixtures_from_func
from lemoncheesecake.suite import load_suites_from_directory
import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *


project_dir = osp.dirname(__file__)


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
        check_that("HTTP status code", req.code, equal_to(200))
         
        content = req.read()
        lcc.log_info("Response body: %s" % content)
        try:
            return json.loads(content)
        except ValueError:
            raise lcc.AbortTest("The returned JSON is not valid")


@lcc.fixture(scope="session")
def omdb(cli_args):
    return OmdbAPI(cli_args.host)


class MyProject(Project):
    def load_suites(self):
        return load_suites_from_directory(osp.join(self.dir, "tests"))

    def load_fixtures(self):
        return load_fixtures_from_func(omdb)

    def add_cli_args(self, cli_parser):
        cli_parser.add_argument("--host", default="www.omdbapi.com", help="omdb API host")


project = MyProject(project_dir)
