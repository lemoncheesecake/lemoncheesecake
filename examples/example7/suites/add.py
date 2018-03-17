import os.path as osp

import json

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

project_dir = osp.join(osp.dirname(__file__), "..")


def test_add(i, j, expected):
    check_that("%d + %d" % (i, j), i + j, equal_to(expected))


@lcc.suite("Add")
class add:
    def __init__(self):
        data = json.load(open(osp.join(project_dir, "data.json")))
        for entry in data:
            lcc.add_test_into_suite(
                lcc.Test(
                    entry["name"], entry["description"], lambda: test_add(entry["i"], entry["j"], entry["expected"])
                ),
                self
            )
