import json

import requests

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *


SUITE = {
    "description": "Echo server tests"
}

URL = "http://localhost:5000/echo"


def test_echo():
    data = {"foo": "bar"}
    lcc.log_info("POST %s %s" % (URL, json.dumps(data)))
    resp = requests.post(URL, json=data)
    require_that("status code", resp.status_code, is_between(200, 299))
    for key, value in data.items():
        check_that_in(resp.json(), key, equal_to(value))


def register_tests(suite, nb_tests):
    for i in range(nb_tests):
        lcc.add_test_into_suite(
            lcc.Test("test_%d" % (i + 1), "Test %d" % (i + 1), test_echo),
            suite
        )


@lcc.suite("Suite 1")
class suite_1:
    def __init__(self):
        register_tests(self, 10)


@lcc.suite("Suite 2")
class suite_2:
    def __init__(self):
        register_tests(self, 10)
