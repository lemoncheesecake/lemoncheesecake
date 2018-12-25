from lemoncheesecake.events import TestSessionSetupEndEvent, TestSessionTeardownEndEvent, \
    TestEndEvent, SuiteSetupEndEvent, SuiteTeardownEndEvent, SuiteEndEvent, SteppedEvent


def _get_testish_info(event, report):
    if isinstance(event, TestEndEvent):
        test_data = report.get_test(event.test)
        return True, test_data.status == "passed"

    if isinstance(event, SuiteSetupEndEvent):
        suite_data = report.get_suite(event.suite)
        return True, suite_data.suite_setup and not suite_data.suite_setup.is_successful()

    if isinstance(event, SuiteTeardownEndEvent):
        suite_data = report.get_suite(event.suite)
        return True, suite_data.suite_teardown and not suite_data.suite_teardown.is_successful()

    if isinstance(event, TestSessionSetupEndEvent):
        return True, report.test_session_setup and not report.test_session_setup.is_successful()

    if isinstance(event, TestSessionTeardownEndEvent):
        return True, report.test_session_teardown and not report.test_session_teardown.is_successful()

    return False, None


def save_at_each_suite_strategy(event, _):
    return isinstance(event, SuiteEndEvent)


def save_at_each_test_strategy(event, report):
    is_testish_end, _ = _get_testish_info(event, report)
    return is_testish_end


def save_at_each_failed_test_strategy(event, report):
    is_testish_end, is_successful = _get_testish_info(event, report)
    return is_testish_end and is_successful


def save_at_each_event_strategy(event, _):
    # "each_event" means events that produces actual data, meaning events that adds data in
    # a step
    return isinstance(event, SteppedEvent)


def make_report_saving_strategy(expression):
    static_expressions = {
        "at_end_of_tests": None,  # no need to an intermediate report saving in this case
        "at_each_suite": save_at_each_suite_strategy,
        "at_each_test": save_at_each_test_strategy,
        "at_each_failed_test": save_at_each_failed_test_strategy,
        "at_each_event": save_at_each_event_strategy
    }

    try:
        return static_expressions[expression]
    except KeyError:
        return ValueError("Unknown report saving strategy expression '%s'" % expression)
