import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *


def naming_scheme(name, description, parameters, idx):
    return "%s_%s" % (name, parameters["word"]), "Check if phrase contains '%s'" % parameters["word"]


@lcc.suite("suite")
class suite:
    @lcc.test("test")
    @lcc.parametrized((
        {"phrase": "i like cakes", "word": "cakes"},
        {"phrase": "cakes with lemon are great", "word": "lemon"}
    ), naming_scheme)
    def test(self, phrase, word):
        check_that("phrase", phrase, contains_string(word))
