import os.path as osp
import json

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

PROJECT_DIR = osp.join(osp.dirname(__file__), "..")


class TestAdd(object):
    def __init__(self, i, j, expected):
        self.i = i
        self.j = j
        self.expected = expected

    def __call__(self):
        check_that(
            "%d + %d" % (self.i, self.j), self.i + self.j, equal_to(self.expected)
        )


@lcc.suite("Add")
class add(object):
    def __init__(self):
        data = json.load(open(osp.join(PROJECT_DIR, "data.json")))
        for entry in data:
            test = lcc.Test(
                entry["name"], entry["description"],
                TestAdd(entry["i"], entry["j"], entry["expected"])
            )
            lcc.add_test_into_suite(test, self)
