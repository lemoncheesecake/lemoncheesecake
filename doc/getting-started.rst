.. _`getting started`:

Getting started
===============

Creating a new test project
---------------------------

Before writing tests, you need to setup a lemoncheesecake project.

The command:

.. code-block:: shell

    $ lcc bootstrap myproject

creates a new project directory "myproject" containing one file "project.py" (it contains your project settings) and
a "suites" directory where you can add your test suites.

Writing a suite
---------------

A suite looks like this:

.. code-block:: python

    # suites/mysuite.py:

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *

    SUITE = {
        "description": "My suite"
    }

    @lcc.test("My test")
    def my_test():
        check_that("value", "foo", equal_to("foo"))

.. note::

    About imports:

    - ``lemoncheesecake.api`` is imported as a module aliased to ``lcc`` and contains the complete lemoncheesecake
      API needed to write tests

    - ``lemoncheesecake.matching`` is imported using a wildcard import to make matching operations more natural to read:

      .. code-block:: python

        # this, is more easier to read:
        check_that("value", 1, is_integer(greater_than(0)))

        # than that:
        lcc.check_that("value", 1, lcc.is_integer(lcc.greater_than(0)))

Using the default ``project.py`` file, suites will be loaded from the ``suites`` sub directory.

Running the tests
-----------------

The command ``lcc run`` is in charge of running the tests, it provides several option to filter the test to be run and
to set the reporting backends that will be used.

.. code-block:: none

    $ lcc.py run --help
    usage: lcc.py run [-h] [--desc DESC [DESC ...]] [--tag TAG [TAG ...]]
                      [--property PROPERTY [PROPERTY ...]]
                      [--link LINK [LINK ...]] [--disabled] [--passed] [--failed]
                      [--skipped] [--enabled] [--from-report FROM_REPORT]
                      [--exit-error-on-failure] [--stop-on-failure]
                      [--report-dir REPORT_DIR]
                      [--reporting REPORTING [REPORTING ...]]
                      [path [path ...]]

    optional arguments:
      -h, --help            show this help message and exit

    Filtering:
      path                  Filter on test/suite path (wildcard character '*' can
                            be used)
      --desc DESC [DESC ...]
                            Filter on descriptions
      --tag TAG [TAG ...], -a TAG [TAG ...]
                            Filter on tags
      --property PROPERTY [PROPERTY ...], -m PROPERTY [PROPERTY ...]
                            Filter on properties
      --link LINK [LINK ...], -l LINK [LINK ...]
                            Filter on links (names and URLs)
      --disabled            Filter on disabled tests
      --passed              Filter on passed tests (only available with --from-report)
      --failed              Filter on failed tests (only available with --from-report)
      --skipped             Filter on skipped tests (only available with --from-report)
      --enabled             Filter on enabled (non-disabled) tests
      --from-report FROM_REPORT
                            When enabled, the filtering is based on the given
                            report

    Test execution:
      --exit-error-on-failure
                            Exit with non-zero code if there is at least one non-
                            passed test
      --stop-on-failure     Stop tests execution on the first non-passed test

    Reporting:
      --report-dir REPORT_DIR, -r REPORT_DIR
                            Directory where report data will be stored
      --reporting REPORTING [REPORTING ...]
                            The list of reporting backends to use
      --save-report SAVE_REPORT
                            At what frequency the reporting backends such as json
                            or xml must save reporting data to disk. (default:
                            $LCC_SAVE_REPORT_AT or at_each_failed_test, possible
                            values are: at_end_of_tests, at_each_suite,
                            at_each_test, at_each_failed_test, at_each_event,
                            every_${N}s)

Tests are run like this:

.. code-block:: none

    $ lcc run
    ============================= my_first_suite ==============================
     OK  1 # some_test

    Statistics :
     * Duration: 0s
     * Tests: 1
     * Successes: 1 (100%)
     * Failures: 0

The generated HTML report is available in the file ``report/report.html``.
