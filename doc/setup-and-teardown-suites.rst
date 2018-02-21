.. _setup_teardown:

Setup and teardown methods
==========================

Test suites provide several methods that give the user the possibility to execute code at particular steps
of the suite execution:

- ``setup_suite`` is called before executing the tests of the suite; if something wrong happens
  (a call to ``log_error`` or a raised exception) then the whole suite execution is aborted

- ``setup_test`` takes the test name as argument and is called before each test,
  if something wrong happen then the test execution is aborted

- ``teardown_test`` is called after each test (it takes the test name as argument),
  if something wrong happens the executed test will be mark as failed

- ``teardown_suite`` is called after executing the tests of the suite

.. note::

    - code within ``setup_suite`` and ``teardown_suite`` methods is executed in a dedicated context and the data
      it generates (checks, logs) will be represented the same way as a test in the test report

    - code within ``setup_test`` and ``teardown_test`` methods is executed within the related test context and the data
      it generates will be associated to the given test
