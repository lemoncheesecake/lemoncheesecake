from lemoncheesecake.matching.matcher import MatcherDescriptionTransformer, MatchDescriptionTransformer


def _test_transformation(actual, conjugate, negative, expected):
    assert MatcherDescriptionTransformer(conjugate, negative)(actual) == expected


def test_to_be():
    _test_transformation("to be great", False, False, "to be great")


def test_to_not_be():
    _test_transformation("to be great", False, True, "to not be great")


def test_is():
    _test_transformation("to be great", True, False, "is great")


def test_is_not():
    _test_transformation("to be great", True, True, "is not great")


def test_to_contain():
    _test_transformation("to contain something", False, False, "to contain something")


def test_to_not_contain():
    _test_transformation("to contain something", False, True, "to not contain something")


def test_contains():
    _test_transformation("to contain something", True, False, "contains something")


def test_does_not_contain():
    _test_transformation("to contain something", True, True, "does not contain something")


def test_MatchDescriptionTransformer_backward_compatibility():
    assert MatchDescriptionTransformer is MatcherDescriptionTransformer
