import os.path as osp
import csv

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

PROJECT_DIR = osp.join(osp.dirname(__file__), "..")


@lcc.suite("suite")
class suite:
    @lcc.test("test")
    @lcc.parametrized(csv.DictReader(open(osp.join(PROJECT_DIR, "data.csv"))))
    def test(self, phrase, word):
        check_that("phrase", phrase, contains_string(word))
