import pytest
from pytest_mock import mocker

from lemoncheesecake.matching.matcher import MatcherDescriptionTransformer


def assert_match_result(matcher, actual, expected_is_successful, expected_details):
    result_details_lst = expected_details if type(expected_details) in (list, tuple) else [expected_details]

    # for now, do nothing with the result, but at least make sure that the function does not raise:
    description = matcher.build_description(MatcherDescriptionTransformer())

    result = matcher.matches(actual)

    assert result.is_successful == expected_is_successful
    for details in result_details_lst:
        assert details in result.description

    return result


def assert_match_success(matcher, actual, result_details=()):
    return assert_match_result(matcher, actual, True, result_details)


def assert_match_failure(matcher, actual, result_details):
    return assert_match_result(matcher, actual, False, result_details)


@pytest.fixture
def log_check_mock(mocker):
    mocked = mocker.patch("lemoncheesecake.matching.operations.log_check")
    return mocked
