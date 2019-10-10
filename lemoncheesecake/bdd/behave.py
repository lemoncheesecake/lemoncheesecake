import os

from slugify import slugify
import six

from lemoncheesecake.reporting import Report, ReportWriter, ReportLocation
from lemoncheesecake.reporting.savingstrategy import make_report_saving_strategy, DEFAULT_REPORT_SAVING_STRATEGY
from lemoncheesecake.reporting.reportdir import create_report_dir_with_rotation
from lemoncheesecake.session import \
    initialize_session, is_location_successful, \
    start_test_session, end_test_session, start_suite, end_suite, start_test, end_test
from lemoncheesecake.suite import Test, Suite
from lemoncheesecake.events import SyncEventManager
from lemoncheesecake.api import set_step


__all__ = (
    "initialize_event_manager",
    "before_all", "after_all",
    "before_feature", "after_feature",
    "before_scenario", "after_scenario",
    "before_step", "after_step"
)


def initialize_event_manager(top_dir, reporting_backends):
    event_manager = SyncEventManager.load()

    report = Report()
    report.nb_threads = 1
    writer = ReportWriter(report)
    event_manager.add_listener(writer)

    report_dir = create_report_dir_with_rotation(top_dir)
    initialize_session(event_manager, report_dir, report)

    report_saving_strategy = make_report_saving_strategy(
        os.environ.get("LCC_SAVE_REPORT", DEFAULT_REPORT_SAVING_STRATEGY)
    )

    for backend in reporting_backends:
        session = backend.create_reporting_session(report_dir, report, False, report_saving_strategy)
        event_manager.add_listener(session)

    return event_manager


def _make_suite_description(feature):
    if feature.description:
        return "Feature: %s\n%s" % (feature.name, "\n".join(feature.description))
    else:
        return "Feature: %s" % feature.name


def _make_suite_name(feature):
    return slugify(feature.name, separator="_")


def _make_test_description(scenario):
    # scenario outlines end with a blank character... strip it:
    scenario_name = scenario.name.strip()
    if scenario.description:
        return "Scenario: %s\n%s" % (scenario_name, "\n".join(scenario.description))
    else:
        return "Scenario: %s" % scenario_name


def _make_test_name(scenario):
    return slugify(scenario.name, separator="_")


def _make_suite_from_feature(feature):
    suite = Suite(
        None, _make_suite_name(feature), _make_suite_description(feature)
    )
    suite.tags.extend(map(six.text_type, feature.tags))
    return suite


def _make_test_from_scenario(scenario, context):
    test = Test(
        _make_test_name(scenario), _make_test_description(scenario), None
    )
    test.parent_suite = context.current_suite
    test.tags.extend(map(six.text_type, scenario.tags))
    return test


def before_all(_):
    start_test_session()


def after_all(_):
    end_test_session()


def before_feature(context, feature):
    context.current_suite = _make_suite_from_feature(feature)
    start_suite(context.current_suite)


def after_feature(context, _):
    end_suite(context.current_suite)


def before_scenario(context, scenario):
    context.current_test = _make_test_from_scenario(scenario, context)
    start_test(context.current_test)


def after_scenario(context, _):
    end_test(context.current_test)


def before_step(_, step):
    set_step(step.keyword + " " + step.name)


def after_step(context, step):
    if not is_location_successful(ReportLocation.in_test(context.current_test)):
        step.hook_failed = True
