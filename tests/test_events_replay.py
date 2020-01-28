from lemoncheesecake.events import SyncEventManager
from lemoncheesecake.reporting.replay import replay_report_events
from lemoncheesecake.reporting import ReportWriter, Report

from helpers.reporttests import ReportingSessionTests, assert_report
from helpers.runner import run_suite_classes


class TestReplayEvents(ReportingSessionTests):
    # it inherits all the actual serialization tests

    def do_test_reporting_session(self, suites, fixtures=(), report_saving_strategy=None):
        if type(suites) not in (list, tuple):
            suites = [suites]
        report = run_suite_classes(
            suites, fixtures=fixtures, report_saving_strategy=report_saving_strategy
        )

        event_manager = SyncEventManager.load()
        new_report = Report()
        writer = ReportWriter(new_report)
        event_manager.add_listener(writer)

        replay_report_events(report, event_manager)

        assert_report(new_report, report, is_persisted=False)
