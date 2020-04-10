###
# The installation hook mechanism has been greatly inspired by allure-behave
# (see: https://github.com/allure-framework/allure-python/blob/master/allure-behave/src/hooks.py)
###

import os
import inspect

from slugify import slugify
import six

from lemoncheesecake.reporting import ReportLocation
from lemoncheesecake.reporting.savingstrategy import make_report_saving_strategy, DEFAULT_REPORT_SAVING_STRATEGY
from lemoncheesecake.reporting.reportdir import create_report_dir_with_rotation
from lemoncheesecake.reporting.backend import get_reporting_backend_names, parse_reporting_backend_names_expression, \
    get_reporting_backends_for_test_run, get_reporting_backends
from lemoncheesecake.session import Session
from lemoncheesecake.suite import Test, Suite
from lemoncheesecake.events import SyncEventManager


_HOOK_NAMES = (
    "before_all", "after_all",
    "before_feature", "after_feature",
    "before_scenario", "after_scenario",
    "before_step", "after_step"
)

_DEFAULT_REPORTING_BACKENDS = "json", "html"


def _wrap_hook(orig, new):
    def hook(*args, **kwargs):
        new(*args, **kwargs)
        return orig(*args, **kwargs)
    return hook


def install_hooks():
    frame_info = inspect.stack()[1]
    namespace = frame_info[0].f_locals
    hooks = _Hooks(os.path.dirname(frame_info[1]))
    for hook_name in _HOOK_NAMES:
        if hook_name in namespace:
            namespace[hook_name] = _wrap_hook(namespace[hook_name], getattr(hooks, hook_name))
        else:
            namespace[hook_name] = getattr(hooks, hook_name)


def _init_reporting_session(top_dir):
    report_dir = os.environ.get("LCC_REPORT_DIR")
    if report_dir:
        os.mkdir(report_dir)
    else:
        report_dir = create_report_dir_with_rotation(top_dir)

    report_saving_strategy = make_report_saving_strategy(
        os.environ.get("LCC_SAVE_REPORT", DEFAULT_REPORT_SAVING_STRATEGY)
    )

    if "LCC_REPORTING" in os.environ:
        try:
            reporting_backend_names = get_reporting_backend_names(
                _DEFAULT_REPORTING_BACKENDS,
                parse_reporting_backend_names_expression(os.environ["LCC_REPORTING"])
            )
        except ValueError as e:
            raise Exception("Invalid $LCC_REPORTING: %s" % e)
    else:
        reporting_backend_names = _DEFAULT_REPORTING_BACKENDS

    reporting_backends = get_reporting_backends_for_test_run(
        {b.get_name(): b for b in get_reporting_backends()}, reporting_backend_names
    )

    return Session.create(SyncEventManager.load(), reporting_backends, report_dir, report_saving_strategy)


class _Hooks(object):
    def __init__(self, top_dir):
        self.top_dir = top_dir
        self.session = None

    @staticmethod
    def _make_suite_description(feature):
        if feature.description:
            return "Feature: %s\n%s" % (feature.name, "\n".join(feature.description))
        else:
            return "Feature: %s" % feature.name

    @staticmethod
    def _make_suite_name(feature):
        return slugify(feature.name, separator="_")

    @staticmethod
    def _make_test_description(scenario):
        # scenario outlines end with a blank character... strip it:
        scenario_name = scenario.name.strip()
        if scenario.description:
            return "Scenario: %s\n%s" % (scenario_name, "\n".join(scenario.description))
        else:
            return "Scenario: %s" % scenario_name

    @staticmethod
    def _make_test_name(scenario):
        return slugify(scenario.name, separator="_")

    @staticmethod
    def _make_suite_from_feature(feature):
        suite = Suite(
            None, _Hooks._make_suite_name(feature), _Hooks._make_suite_description(feature)
        )
        suite.tags.extend(map(six.text_type, feature.tags))
        return suite

    @staticmethod
    def _make_test_from_scenario(scenario, context):
        test = Test(
            _Hooks._make_test_name(scenario), _Hooks._make_test_description(scenario), None
        )
        test.parent_suite = context.current_suite
        test.tags.extend(map(six.text_type, scenario.tags))
        return test

    def before_all(self, _):
        self.session = _init_reporting_session(self.top_dir)
        self.session.start_test_session()

    def after_all(self, _):
        self.session.end_test_session()

    def before_feature(self, context, feature):
        context.current_suite = _Hooks._make_suite_from_feature(feature)
        self.session.start_suite(context.current_suite)

    def after_feature(self, context, _):
        self.session.end_suite(context.current_suite)

    def before_scenario(self, context, scenario):
        context.current_test = _Hooks._make_test_from_scenario(scenario, context)
        self.session.start_test(context.current_test)

    def after_scenario(self, context, _):
        self.session.end_test(context.current_test)

    def before_step(self, _, step):
        self.session.set_step(step.keyword + " " + step.name)

    def after_step(self, context, step):
        if not self.session.is_successful(ReportLocation.in_test(context.current_test)):
            step.hook_failed = True
