.. _`tests and suites`:

Tests and suites
================

Defining a suite
----------------

A suite can be either represented by:

- a module (in this case the module must define a ``SUITE`` variable that contains at least
  the ``"description"`` key), each test is a function decorated with ``@lcc.test``:

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

- a class (in this case the class name must match the module name), each test is a method decorated with ``@lcc.test``:

  .. code-block:: python

      # suites/mysuite.py:

      import lemoncheesecake.api as lcc
      from lemoncheesecake.matching import *

      @lcc.suite("My suite")
      class mysuite:
          @lcc.test("My test")
          def my_test(self):
              check_that("value", "foo", equal_to("foo"))

A suite can be nested in another suite, it can be performed in different ways:

- as a class in a suite module:

  .. code-block:: python

      # suites/mysuite.py:

      SUITE = {
        "description": "Parent suite"
      }

      @lcc.test("Test A")
      def test_a():
          pass

      @lcc.suite("Child suite 1")
      class child_suite_1:
          @lcc.test("Test B")
          def test_b(self):
              pass

      @lcc.suite("Child suite 2")
      class child_suite_2:
          @lcc.test("Test C")
          def test_c(self):
              pass

- as a nested class:

  .. code-block:: python

      # suites/mysuite.py:

      @lcc.suite("Parent suite")
      class parent_suite:
          @lcc.suite("Child suite")
          class child_suite:
              pass

- as a module in a sub directory whose name matches the parent suite module:

  .. code-block:: text

      $ tree
      .
      ├── parent_suite
      │   └── child_suite.py
      └── parent_suite.py

      1 directory, 2 files

Adding metadata to tests and suites
-----------------------------------

Several type of metadata can be associated to both tests and suites using decorators:

- ``tags`` (take one or more tag name as argument):

  .. code-block:: python

      @lcc.test("Test something")
      @lcc.tags("important")
      def test_something():
          pass

      @lcc.test("Test something else")
      @lcc.tags("slow")
      def test_something_else():
          pass

      @lcc.test("Test something else again")
      @lcc.tags("slow", "deprecated")
      def test_something_else_again():
          pass

- ``properties`` (take a key/value pair arguments):

  .. code-block:: python

      @lcc.test("Test something")
      @lcc.prop("type", "acceptance")
      def test_something(self):
          pass

      @lcc.test("Test something else")
      @lcc.prop("type", "destructive")
      def test_something_else(self):
          pass

- ``links`` (take an URL and an optional description as arguments):

  .. code-block:: python

      @lcc.test("Test something")
      @lcc.link("http://bugtracker.example.com/issues/1234", "TICKET-1234")
      def test_something():
          pass

      @lcc.test("Test something else")
      @lcc.link("http://bugtracker.example.com/issues/5678")
      def test_something_else():
          pass

Metadata can also be associated to a suite module using the ``SUITE`` variable:

.. code-block:: python

    SUITE = {
        "description": "My Suite",
        "tags": ["slow"]
    }

Once, the metadata are set, they:

- can be used as :ref:`filters <cli_filters>` in the various lemoncheesecake :ref:`CLI tools <cli>`

- will be available in the test report


Disabling a test or a suite
---------------------------

A test or an entire suite can be disabled using the ``@lcc.disabled()`` decorator::

    @lcc.test("Test something")
    @lcc.disabled()
    def test_something(self):
        pass

Disabled tests are visible in the report but they are not taken into account while computing the percentage
of successful tests.

*Since version 1.1.0*, it's possible to pass a ``reason`` (str) argument to the decorator, it will be visible
in the generated report.

If you want to completely hide a test or a suite from the test tree and the report, use ``@lcc.hidden()``.

Conditional tests and suites
----------------------------

A test or an entire suite can included or excluded from the test tree using the ``@lcc.visible_if(condition)`` decorator.

This decorator can be associated to both tests and suites, it takes a callable as argument. This callable will
be called with the object to which it is associated (a module, a class or a function).
If the callable return a non-true value, then the test/suite
won't be included in the test tree, meaning it won't be executed, it won't be present in the test report nor in the
``lcc show`` command output.

Usage::

    @lcc.suite("My Suite")
    class mysuite:
        some_feature_enabled = True

        @lcc.test("Test something")
        @lcc.visible_if(lambda test: mysuite.some_feature_enabled)
        def test_something(self):
            pass

Dependency between tests
------------------------

Dependency between tests can be added using the ``@lcc.depends_on(*test_paths)`` decorator::

    @lcc.suite("My Suite")
    class mysuite:
        @lcc.test("Test 1")
        def test_1():
            pass

        @lcc.test("Test 2")
        @lcc.depends_on("mysuite.test_1")
        def test_2():
            pass

If "mysuite.test_1" fails, then "mysuite.test_2" will be skipped.

This decorator:

- can take multiple test paths

- it is only applicable to tests (not suites)

- the test path must point to a test (not a suite)
