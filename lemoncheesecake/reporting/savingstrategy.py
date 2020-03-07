import re
import time

from lemoncheesecake.events import TestSessionSetupEndEvent, TestSessionTeardownEndEvent, \
    TestEndEvent, SuiteSetupEndEvent, SuiteTeardownEndEvent, SuiteEndEvent, SteppedEvent
from lemoncheesecake.reporting.report import ReportLocation

DEFAULT_REPORT_SAVING_STRATEGY = "at_each_failed_test"


def _is_end_of_result_event(event):
    if isinstance(event, TestEndEvent):
        return ReportLocation.in_test(event.test)

    if isinstance(event, SuiteSetupEndEvent):
        return ReportLocation.in_suite_setup(event.suite)

    if isinstance(event, SuiteTeardownEndEvent):
        return ReportLocation.in_suite_teardown(event.suite)

    if isinstance(event, TestSessionSetupEndEvent):
        return ReportLocation.in_test_session_setup()

    if isinstance(event, TestSessionTeardownEndEvent):
        return ReportLocation.in_test_session_teardown()

    return None


def save_at_each_suite_strategy(event, _):
    return isinstance(event, SuiteEndEvent)


def save_at_each_test_strategy(event, _):
    return _is_end_of_result_event(event) is not None


def save_at_each_failed_test_strategy(event, report):
    location = _is_end_of_result_event(event)
    if location:
        result = report.get(location)
        return result and result.status == "failed"
    else:
        return False


def save_at_each_log_strategy(event, _):
    return isinstance(event, SteppedEvent)


class SaveAtInterval(object):
    def __init__(self, interval):
        self.interval = interval
        self.last_saving = None

    def __call__(self, event, report):
        now = time.time()
        if self.last_saving:
            must_be_saved = now > self.last_saving + self.interval
            if must_be_saved:
                self.last_saving = now
            return must_be_saved
        else:
            self.last_saving = now  # not a saving but an initialization
            return False


def make_report_saving_strategy(expression):
    # first, try with a static expression
    static_expressions = {
        "at_end_of_tests": None,  # no need to an intermediate report saving in this case
        "at_each_suite": save_at_each_suite_strategy,
        "at_each_test": save_at_each_test_strategy,
        "at_each_failed_test": save_at_each_failed_test_strategy,
        "at_each_log": save_at_each_log_strategy,
        "at_each_event": save_at_each_log_strategy  # deprecated since 1.4.5, "at_each_log" must be used instead
    }

    try:
        return static_expressions[expression]
    except KeyError:
        pass

    # second, try with "every_Ns"
    m = re.compile(r"^every[_ ](\d+)s$").match(expression)
    if m:
        return SaveAtInterval(int(m.group(1)))

    # ok... nothing we know about
    raise ValueError("Invalid expression '%s' for report saving strategy" % expression)
