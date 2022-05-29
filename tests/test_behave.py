# -*- coding: utf-8 -*-

try:
    from behave.__main__ import main as behave_main

except ImportError:
    pass  # no behave tests if behave is not available

else:
    import os
    import os.path as osp

    import pytest

    from lemoncheesecake.reporting import load_report
    from lemoncheesecake.bdd.behave import _init_reporting_session
    from helpers.report import get_last_test, get_last_suite
    from helpers.utils import env_vars, change_dir

    STEPS = """# -*- coding: utf-8 -*-
from behave import *

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *


@given("a is {value:d}")
def step_impl(context, value):
    context.a = value
    lcc.log_info("a = %s" % value)


@given("a is {value:d} éà")
def step_impl(context, value):
    context.a = value
    lcc.log_info("a = %s" % value)


@given("b is {value:d}")
def step_impl(context, value):
    context.b = value
    lcc.log_info("b = %s" % value)


@then("a + b is equal to {value:d}")
def step_impl(context, value):
    check_that("%s + %s" % (context.a, context.b), context.a + context.b, equal_to(value))
"""

    def run_behave_tests(tmpdir, feature_content, step_content, env_content=None, expected_report_dir=None):
        tmpdir.mkdir("features").join("feature.feature").write_text(feature_content, "utf-8")
        tmpdir.mkdir("steps").join("step.py").write_text(step_content, "utf-8")
        if not env_content:
            env_content = """from lemoncheesecake.bdd.behave import install_hooks
install_hooks()
"""
        tmpdir.join("environment.py").write_text(env_content, "utf-8")

        with change_dir(tmpdir.strpath):
            behave_main([osp.join("features", "feature.feature")])

        if not expected_report_dir:
            expected_report_dir = tmpdir.join("report").strpath
        return load_report(expected_report_dir)


    def test_init_reporting_session(tmpdir):
        with change_dir(tmpdir.strpath):
            _init_reporting_session(".")

    def test_init_reporting_session_with_valid_custom_report_saving_strategy(tmpdir):
        with change_dir(tmpdir.strpath):
            with env_vars(LCC_SAVE_REPORT="at_each_test"):
                _init_reporting_session(".")

    def test_init_reporting_session_with_invalid_custom_report_saving_strategy(tmpdir):
        with change_dir(tmpdir.strpath):
            with env_vars(LCC_SAVE_REPORT="foobar"):
                with pytest.raises(ValueError, match="Invalid expression"):
                    _init_reporting_session(".")

    def test_scenario_passed(tmpdir):
        feature = """Feature: do some computations
    
Scenario: do a simple addition
    Given a is 2
    And b is 2
    Then a + b is equal to 4
"""

        report = run_behave_tests(tmpdir, feature, STEPS)

        test = get_last_test(report)
        assert test.parent_suite.name == "do_some_computations"
        assert test.parent_suite.description == "Feature: do some computations"
        assert test.status == "passed"
        assert test.name == "do_a_simple_addition"
        assert test.description == "Scenario: do a simple addition"
        steps = test.get_steps()
        assert steps[0].description == "Given a is 2"
        assert steps[0].get_logs()[0].message == "a = 2"
        assert steps[1].description == "And b is 2"
        assert steps[1].get_logs()[0].message == "b = 2"
        assert steps[2].description == "Then a + b is equal to 4"
        assert steps[2].get_logs()[0].description == "Expect 2 + 2 to be equal to 4"
        assert steps[2].get_logs()[0].is_successful is True


    def test_scenario_failed(tmpdir):
        feature = """Feature: do some computations
    
Scenario: do a simple addition
    Given a is 2
    And b is 2
    Then a + b is equal to 5
"""

        report = run_behave_tests(tmpdir, feature, STEPS)

        test = get_last_test(report)
        assert test.parent_suite.name == "do_some_computations"
        assert test.parent_suite.description == "Feature: do some computations"
        assert test.status == "failed"
        assert test.name == "do_a_simple_addition"
        assert test.description == "Scenario: do a simple addition"
        steps = test.get_steps()
        assert steps[0].description == "Given a is 2"
        assert steps[0].get_logs()[0].message == "a = 2"
        assert steps[1].description == "And b is 2"
        assert steps[1].get_logs()[0].message == "b = 2"
        assert steps[2].description == "Then a + b is equal to 5"
        assert steps[2].get_logs()[0].description == "Expect 2 + 2 to be equal to 5"
        assert steps[2].get_logs()[0].is_successful is False


    def test_scenario_unicode(tmpdir):
        feature = """Feature: do some computations éà
    
Scenario: do a simple addition éà
    Given a is 2 éà
    And b is 2
    Then a + b is equal to 4
"""

        report = run_behave_tests(tmpdir, feature, STEPS)

        test = get_last_test(report)
        assert test.parent_suite.name == "do_some_computations_ea"
        assert test.parent_suite.description == "Feature: do some computations éà"
        assert test.status == "passed"
        assert test.name == "do_a_simple_addition_ea"
        assert test.description == "Scenario: do a simple addition éà"
        steps = test.get_steps()
        assert steps[0].description == "Given a is 2 éà"
        assert steps[0].get_logs()[0].message == "a = 2"
        assert steps[1].description == "And b is 2"
        assert steps[1].get_logs()[0].message == "b = 2"
        assert steps[2].description == "Then a + b is equal to 4"
        assert steps[2].get_logs()[0].description == "Expect 2 + 2 to be equal to 4"
        assert steps[2].get_logs()[0].is_successful is True


    def test_tags(tmpdir):
        feature = """@tag1
Feature: do some computations

@tag2
Scenario: do a simple addition
    Given a is 2
    And b is 2
    Then a + b is equal to 4
"""

        report = run_behave_tests(tmpdir, feature, STEPS)

        test = get_last_test(report)
        assert test.parent_suite.tags == ["tag1"]
        assert test.tags == ["tag2"]


    def test_scenario_outline(tmpdir):
        feature = """Feature: do some computations
    
  Scenario Outline: addition
    Given a is <a>
    Given b is <b>
    Then a + b is equal to <c>

   Examples:
       | a | b | c |
       | 2 | 2 | 4 |
       | 1 | 1 | 3 |
       | 1 | 5 | 6 |
"""

        report = run_behave_tests(tmpdir, feature, STEPS)

        suite = get_last_suite(report)
        test_1, test_2, test_3 = suite.get_tests()

        assert test_1.name == "addition_1_1"
        assert test_1.description == "Scenario: addition -- @1.1"
        assert test_1.status == "passed"

        assert test_2.name == "addition_1_2"
        assert test_2.description == "Scenario: addition -- @1.2"
        assert test_2.status == "failed"

        assert test_3.name == "addition_1_3"
        assert test_3.description == "Scenario: addition -- @1.3"
        assert test_3.status == "passed"

    def test_custom_report_dir(tmpdir):
        feature = """Feature: do some computations

        Scenario: do a simple addition
            Given a is 2
            And b is 2
            Then a + b is equal to 4
        """

        report_dir = os.path.join(tmpdir.strpath, "custom_report_dir")
        with env_vars(LCC_REPORT_DIR=report_dir):
            report = run_behave_tests(tmpdir, feature, STEPS, expected_report_dir=report_dir)

        assert report is not None

    def test_custom_reporting(tmpdir):
        feature = """Feature: do some computations

        Scenario: do a simple addition
            Given a is 2
            And b is 2
            Then a + b is equal to 4
        """

        with env_vars(LCC_REPORTING="-html"):
            run_behave_tests(tmpdir, feature, STEPS)

        assert tmpdir.join("report", "report.js").exists()
        assert not tmpdir.join("report", "report.html").exists()

    def test_play_well_with_existing_hook(tmpdir):
        feature = """Feature: do some computations

        Scenario: do a simple addition
            Given a is 2
            And b is 2
            Then a + b is equal to 4
        """
        env = """import os
import os.path
from lemoncheesecake.bdd.behave import install_hooks

def after_all(_):
    os.mkdir(os.path.join(r"{tmpdir}", "iwashere"))

install_hooks()
""".format(tmpdir=tmpdir.strpath)

        with env_vars(LCC_REPORTING="-html"):
            run_behave_tests(tmpdir, feature, STEPS, env_content=env)

        assert tmpdir.join("report", "report.js").exists()
        assert not tmpdir.join("report", "report.html").exists()
        assert tmpdir.join("iwashere").exists()
