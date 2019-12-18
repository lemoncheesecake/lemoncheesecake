import os.path as osp
import json

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

PROJECT_DIR = osp.join(osp.dirname(__file__), "..")


@lcc.suite("suite")
class suite:
    @lcc.test("test")
    @lcc.parametrized(json.load(open(osp.join(PROJECT_DIR, "data.json"))))
    def test(self, phrase, word):
        check_that("phrase", phrase, contains_string(word))
