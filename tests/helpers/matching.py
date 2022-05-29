from unittest.mock import patch

import pytest
from pytest_mock import mocker
from callee import Any

from lemoncheesecake.matching import check_that
from lemoncheesecake.matching.matcher import MatcherDescriptionTransformer


def assert_match_result(matcher, actual, expected_is_successful, expected_details):
    with patch("lemoncheesecake.matching.operations.log_check") as mocked:
        result = check_that("value", actual, matcher)
    mocked.assert_called_with(Any(), expected_is_successful, expected_details)
    return result


def assert_match_success(matcher, actual, result_details=Any()):
    return assert_match_result(matcher, actual, True, result_details)


def assert_match_failure(matcher, actual, result_details):
    return assert_match_result(matcher, actual, False, result_details)


def assert_matcher_description(matcher, expected, transformer=MatcherDescriptionTransformer()):
    assert matcher.build_description(transformer) == expected


@pytest.fixture
def log_check_mock(mocker):
    return mocker.patch("lemoncheesecake.matching.operations.log_check")
