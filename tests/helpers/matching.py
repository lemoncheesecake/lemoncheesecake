import lemoncheesecake.api as lcc

from helpers.runner import run_func_in_test, get_reporting_session


def assert_match_result(matcher, actual, result_outcome, result_details):
    result_details_lst = result_details if type(result_details) in (list, tuple) else [result_details]

    reporting_session = get_reporting_session()
    run_func_in_test(lambda: lcc.check_that("value", actual, matcher))
    assert reporting_session.last_check_outcome == result_outcome
    for details in result_details_lst:
        assert details in reporting_session.last_check_details


def assert_match_success(matcher, actual, result_details):
    assert_match_result(matcher, actual, True, result_details)


def assert_match_failure(matcher, actual, result_details):
    assert_match_result(matcher, actual, False, result_details)
