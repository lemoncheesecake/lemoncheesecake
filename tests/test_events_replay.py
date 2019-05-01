import pytest

from lemoncheesecake.events import SyncEventManager
from lemoncheesecake.reporting.replay import replay_report_events
from lemoncheesecake.reporting import ReportWriter

from helpers.reporttests import *  # import the actual tests against JSON serialization


def _test_serialization(suites_or_report, _, __, fixtures=(), report_saving_strategy=None):
    if isinstance(suites_or_report, Report):
        report = suites_or_report
    else:
        suites = suites_or_report
        if type(suites) not in (list, tuple):
            suites = [suites]
        report = run_suite_classes(
            suites, fixtures=fixtures, report_saving_strategy=report_saving_strategy
        )

#     dump_report(unserialized_report)

    event_manager = SyncEventManager.load()
    new_report = Report()
    writer = ReportWriter(new_report)
    event_manager.add_listener(writer)

    replay_report_events(report, event_manager)

    assert_report(new_report, report, is_persisted=False)


@pytest.fixture(scope="function")
def backend():
    return None


@pytest.fixture()
def serialization_tester():
    return _test_serialization
