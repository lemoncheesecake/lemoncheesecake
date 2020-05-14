.. _`getting started`:

Getting started
===============

Create a "suites" directory and add a suite module :

.. code-block:: python

    # suites/my_suite.py:

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *

    @lcc.test()
    def my_test():
        check_that("value", "foo", equal_to("foo"))

Then, run the tests :

.. code-block:: none

    $ lcc run
    ================================== my_suite ===================================
     OK  1 # my_suite.my_test

    Statistics :
     * Duration: 0.034s
     * Tests: 1
     * Successes: 1 (100%)
     * Failures: 0

The generated HTML report is available in the file ``report/report.html``.

The report can also be viewed directly on the terminal:

.. code-block:: none

    $ lcc report
    PASSED: My test
    (my_suite.my_test)
    +----------+-----------------------------------+-----------+
    |          | My test                           | 0.001s    |
    +----------+-----------------------------------+-----------+
    | CHECK OK | Expect value to be equal to "foo" | Got "foo" |
    +----------+-----------------------------------+-----------+

``lcc run`` provides plenty of options on test filtering, test execution and reporting.
All the details about this command can be found :ref:`here <lcc_run>`.

.. note::

    About imports:

    - ``lemoncheesecake.api`` is imported as a module aliased to ``lcc`` and contains the complete lemoncheesecake
      API needed to write tests

    - ``lemoncheesecake.matching`` is imported using a wildcard import to make matching operations more pleasant to read:

      .. code-block:: python

        # this, is more easier to read:
        check_that("value", 1, is_integer(greater_than(0)))

        # than that:
        lcc.check_that("value", 1, lcc.is_integer(lcc.greater_than(0)))
