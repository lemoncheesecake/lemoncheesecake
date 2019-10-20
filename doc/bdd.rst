.. _bdd:

BDD using behave
================

.. versionadded:: 1.3.0

lemoncheesecake is a framework where tests are written in pure Python either as functions or methods.
It does not aim to be a BDD tool. However, since version 1.3.0, it provides an integration
with `behave <https://behave.readthedocs.io/en/latest/>`_.

This integration allows :ref:`logging functions <logging>`, :ref:`matchers <matchers>` to be used
within behave's steps. This integration also benefit from the various lemoncheesecake reporting backends
(Slack, ReportPortal, among others).

No extra dependency are required besides lemoncheesecake and behave.

The rest of the document assumes that the reader already knows about
`writing tests with behave <https://behave.readthedocs.io/en/latest/tutorial.html>`_.

Setup
-----

lemoncheesecake uses `behave hook system <https://behave.readthedocs.io/en/latest/tutorial.html#environmental-controls>`_
to create a report with suites, tests, etc...

The ``environment.py`` file must integrate a call to ``install_hook``, like this::

    # file: environment.py

    from lemoncheesecake.bdd.behave import install_hooks

    install_hooks()

If you have defined your own hooks (such as ``before_feature``, ``before_scenario``, etc...), they will be preserved
by ``install_hooks``.

Example
-------

Giving this feature file:

.. code-block:: gherkin

    # file: features/calc.feature

    Feature: calc

      Scenario: two plus two
        Given a is 2
        Given b is 2
        Then a + b is equal to 4

      Scenario Outline: more calc
        Given a is <a>
        Given b is <b>
        Then a + b is equal to <c>

        Examples:
           | a | b | c |
           | 3 | 2 | 5 |
           | 1 | 5 | 6 |

And this step file::

    # file: steps/calc.py

    from behave import *

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *


    @given("a is {value:d}")
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

Tests can be run:

.. code-block:: console

    $ behave
    Feature: calc # features/calc.feature:3

      Scenario: two plus two     # features/calc.feature:5
        Given a is 2             # steps/calc.py:7 0.000s
        Given b is 2             # steps/calc.py:13 0.000s
        Then a + b is equal to 4 # steps/calc.py:19 0.000s

      Scenario Outline: more calc -- @1.1   # features/calc.feature:17
        Given a is 3                        # steps/calc.py:7 0.000s
        Given b is 2                        # steps/calc.py:13 0.000s
        Then a + b is equal to 5            # steps/calc.py:19 0.000s

      Scenario Outline: more calc -- @1.2   # features/calc.feature:18
        Given a is 1                        # steps/calc.py:7 0.000s
        Given b is 5                        # steps/calc.py:13 0.000s
        Then a + b is equal to 6            # steps/calc.py:19 0.000s

    1 feature passed, 0 failed, 0 skipped
    3 scenarios passed, 0 failed, 0 skipped
    9 steps passed, 0 failed, 0 skipped, 0 undefined
    Took 0m0.002s

The corresponding lemoncheesecake report as displayed by ``lcc report``:

.. code-block:: console

    $ lcc report -e
    PASSED: Scenario: two plus two
    (calc.two_plus_two)
    +----------+-------------------------------+--------+
    |          | Given a is 2                  | 0.001s |
    +----------+-------------------------------+--------+
    |   INFO   | a = 2                         |        |
    +----------+-------------------------------+--------+
    |          | Given b is 2                  | 0.001s |
    +----------+-------------------------------+--------+
    |   INFO   | b = 2                         |        |
    +----------+-------------------------------+--------+
    |          | Then a + b is equal to 4      | 0.000s |
    +----------+-------------------------------+--------+
    | CHECK OK | Expect 2 + 2 to be equal to 4 | Got 4  |
    +----------+-------------------------------+--------+

    PASSED: Scenario: more calc -- @1.1
    (calc.more_calc_1_1)
    +----------+-------------------------------+--------+
    |          | Given a is 3                  | 0.000s |
    +----------+-------------------------------+--------+
    |   INFO   | a = 3                         |        |
    +----------+-------------------------------+--------+
    |          | Given b is 2                  | 0.001s |
    +----------+-------------------------------+--------+
    |   INFO   | b = 2                         |        |
    +----------+-------------------------------+--------+
    |          | Then a + b is equal to 5      | 0.000s |
    +----------+-------------------------------+--------+
    | CHECK OK | Expect 3 + 2 to be equal to 5 | Got 5  |
    +----------+-------------------------------+--------+

    PASSED: Scenario: more calc -- @1.2
    (calc.more_calc_1_2)
    +----------+-------------------------------+--------+
    |          | Given a is 1                  | 0.000s |
    +----------+-------------------------------+--------+
    |   INFO   | a = 1                         |        |
    +----------+-------------------------------+--------+
    |          | Given b is 5                  | 0.000s |
    +----------+-------------------------------+--------+
    |   INFO   | b = 5                         |        |
    +----------+-------------------------------+--------+
    |          | Then a + b is equal to 6      | 0.001s |
    +----------+-------------------------------+--------+
    | CHECK OK | Expect 1 + 5 to be equal to 6 | Got 6  |
    +----------+-------------------------------+--------+


Reporting configuration
-----------------------

Reporting can be configured through the following environment variables:

- ``LCC_REPORT_DIR``: see :option:`lcc run --report-dir <--report-dir>`

- ``LCC_REPORTING``: see :option:`lcc run --reporting <--reporting>`, please note that the default reporting backends
  used for behave test runs are ``json`` and ``html``

- ``LCC_SAVE_REPORT``: see :option:`lcc run --save-report <--save-report>`
