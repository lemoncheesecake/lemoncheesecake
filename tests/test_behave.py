# -*- coding: utf-8 -*-

try:
    import behave

except ImportError:
    pass  # no behave tests if behave is not available

else:
    import os

    from lemoncheesecake.reporting import load_report
    from helpers.report import get_last_test, get_last_suite

    STEPS = u"""# -*- coding: utf-8 -*-
from behave import *

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *


@given("a is {value:d}")
def step_impl(context, value):
    context.a = value
    lcc.log_info("a = %s" % value)


@given(u"a is {value:d} éà")
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

    def run_behave_tests(tmpdir, feature_content, step_content):
        tmpdir.mkdir("features").join("feature.feature").write_text(feature_content, "utf-8")
        tmpdir.mkdir("steps").join("step.py").write_text(step_content, "utf-8")
        tmpdir.join("environment.py").write_text(u"""from __future__ import print_function
    
import os.path

from lemoncheesecake.bdd.behave import *
from lemoncheesecake.reporting import get_reporting_backend_by_name


initialize_event_manager(
    os.path.dirname(__file__),
    list(map(get_reporting_backend_by_name, ("json",)))
)
""", "utf-8")

        cmd = "behave %s" % tmpdir.join("features").join("feature.feature   ").strpath
        os.system(cmd)

        return load_report(tmpdir.join("report").strpath)


    def test_scenario_passed(tmpdir):
        feature = u"""Feature: do some computations
    
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
        assert steps[0].entries[0].message == "a = 2"
        assert steps[1].description == "And b is 2"
        assert steps[1].entries[0].message == "b = 2"
        assert steps[2].description == "Then a + b is equal to 4"
        assert steps[2].entries[0].description == "Expect 2 + 2 to be equal to 4"
        assert steps[2].entries[0].is_successful is True


    def test_scenario_failed(tmpdir):
        feature = u"""Feature: do some computations
    
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
        assert steps[0].entries[0].message == "a = 2"
        assert steps[1].description == "And b is 2"
        assert steps[1].entries[0].message == "b = 2"
        assert steps[2].description == "Then a + b is equal to 5"
        assert steps[2].entries[0].description == "Expect 2 + 2 to be equal to 5"
        assert steps[2].entries[0].is_successful is False


    def test_scenario_unicode(tmpdir):
        feature = u"""Feature: do some computations éà
    
Scenario: do a simple addition éà
    Given a is 2 éà
    And b is 2
    Then a + b is equal to 4
"""

        report = run_behave_tests(tmpdir, feature, STEPS)

        test = get_last_test(report)
        assert test.parent_suite.name == "do_some_computations_ea"
        assert test.parent_suite.description == u"Feature: do some computations éà"
        assert test.status == "passed"
        assert test.name == "do_a_simple_addition_ea"
        assert test.description == u"Scenario: do a simple addition éà"
        steps = test.get_steps()
        assert steps[0].description == u"Given a is 2 éà"
        assert steps[0].entries[0].message == "a = 2"
        assert steps[1].description == "And b is 2"
        assert steps[1].entries[0].message == "b = 2"
        assert steps[2].description == "Then a + b is equal to 4"
        assert steps[2].entries[0].description == "Expect 2 + 2 to be equal to 4"
        assert steps[2].entries[0].is_successful is True


    def test_tags(tmpdir):
        feature = u"""@tag1
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
        feature = u"""Feature: do some computations
    
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
