def assert_match_result(matcher, actual, result_outcome, result_details):
    result_details_lst = result_details if type(result_details) in (list, tuple) else [result_details]

    # for now, do nothing with the result, but at least make sure that the function does not raise:
    description = matcher.build_description()

    result = matcher.matches(actual)

    assert result.outcome == result_outcome
    for details in result_details_lst:
        assert details in result.description

    return result


def assert_match_success(matcher, actual, result_details=()):
    return assert_match_result(matcher, actual, True, result_details)


def assert_match_failure(matcher, actual, result_details):
    return assert_match_result(matcher, actual, False, result_details)
