import os.path as osp
import json

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

PROJECT_DIR = osp.join(osp.dirname(__file__), "..")


@lcc.suite("Add")
class add:
    def __init__(self):
        data = json.load(open(osp.join(PROJECT_DIR, "data.json")))
        for entry in data:
            test = lcc.Test(
                entry["name"], entry["description"],
                self.make_test_func(entry["i"], entry["j"], entry["expected"])
            )
            lcc.add_test_into_suite(test, self)

    @staticmethod
    def make_test_func(i, j, expected):
        def func():
            check_that("%d + %d" % (i, j), i + j, equal_to(expected))
        return func
