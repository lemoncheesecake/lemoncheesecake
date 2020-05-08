.. _`tests and suites`:

Writing tests
=============

Test as a function
------------------

Here is a very simple example of a suite:

.. code-block:: python

    # suites/my_suite.py:

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *

    @lcc.test()
    def my_test_1():
        check_that("value", "foo", equal_to("foo"))

    @lcc.test()
    def my_test_2():
        check_that("value", "bar", equal_to("bar"))


.. code-block:: text

    $ lcc show
    * my_suite
        - my_suite.my_test_1
        - my_suite.my_test_2

A test is a function (or a method, see later) decorated with ``@lcc.test()``.

Test as a method
----------------

Tests can also be implemented as class methods:

.. code-block:: python

    # suites/my_suite.py:

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *

    @lcc.suite()
    class suite_a:
        @lcc.test()
        def my_test_1():
            check_that("value", "foo", equal_to("foo"))

    @lcc.suite()
    class suite_b:
        @lcc.test()
        def my_test_1():
            check_that("value", "bar", equal_to("bar"))

.. code-block:: text

    $ lcc show
    * my_suite
        * my_suite.suite_a
            - my_suite.suite_a.my_test_1
        * my_suite.suite_b
            - my_suite.suite_b.my_test_1

In that case, the class must be decorated with ``@lcc.suite()`` and will be considered as a sub-suite of the current
module-suite.

Please note that if the module only contains one suite-class whose name is equal to the module's name, then this suite will
not be considered as a sub-suite of the module-suite, but as the suite itself:

.. code-block:: python

    # suites/my_suite.py:

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *

    @lcc.suite()
    class my_suite:
        @lcc.test()
        def my_test_1():
            check_that("value", "foo", equal_to("foo"))

        @lcc.test()
        def my_test_2():
            check_that("value", "bar", equal_to("bar"))

.. code-block:: text

    $ lcc show
    * my_suite
        - my_suite.my_test_1
        - my_suite.my_test_2


Organizing suites within directories
------------------------------------

Suites hierarchy can also be created through putting modules into sub-directories, such as this:

.. code-block:: python

    # suites/parent_suite.py:

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *

    @lcc.test()
    def test_in_parent_suite():
        check_that("value", "foo", equal_to("foo"))


    # suites/parent_suite/child_suite.py:

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *

    @lcc.test()
    def test_in_child_suite():
        check_that("value", "foo", equal_to("foo"))

.. code-block:: text

    .
    └── suites
        ├── parent_suite
        │   └── child_suite.py
        └── parent_suite.py

.. code-block:: text

    $ lcc show
    * parent_suite
        - parent_suite.test_in_parent_suite
        * parent_suite.child_suite
            - parent_suite.child_suite.test_in_child_suite

A directory without a ``*.py`` associated file, will be also considered as a suite:

.. code-block:: python

    # suites/parent_suite/child_suite.py:

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *

    @lcc.test()
    def test_in_child_suite():
        check_that("value", "foo", equal_to("foo"))

.. code-block:: text

    .
    └── suites
        └── parent_suite
            └── child_suite.py

.. code-block:: text

    $ lcc show
    * parent_suite
        * parent_suite.child_suite
            - parent_suite.child_suite.test_in_child_suite

.. versionchanged:: 1.5.0

Since version 1.5.0, several prior requirements have been made optional:

- the description for tests and suites is now optional

- the ``SUITE`` variable in module is now optional

- suites can be created with only a directory containing ``*.py`` files, a ``*.py`` file companion is no longer a requirement,
  in other words: for a ``parent_suite`` directory a ``parent_suite.py`` file (at the same level) is no longer mandatory

Metadata
--------

Metadata can be associated to both tests and suites, they can be used to :ref:`filter tests <cli_filters>` and will
be displayed in the report:

- description (a description is generated from the test/suite name by default)

- tags

- properties (key/value pairs)

- link (an URL and an optional description)

Example:

.. code-block:: python

    @lcc.test("A test with a meaningful description")
    @lcc.tags("important")
    @lcc.tags("a_second_tag", "a_third_tag")
    @lcc.prop("type", "acceptance")
    @lcc.link("http://bugtracker.example.com/issues/1234", "TICKET-1234")
    @lcc.link("http://bugtracker.example.com/issues/1235")
    def my_test():
        check_that("value", "foo", equal_to("foo"))

The ``@lcc.suite()`` decorator also takes a description like ``@lcc.test()`` does.

The ``@lcc.tags()``, ``@lcc.prop()`` and ``@lcc.link()`` decorators also apply to suite-classes.

In suite-modules, metadata are be set through a ``SUITE`` module-level variable:

.. code-block:: python

    # suites/my_suite.py

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *

    SUITE = {
        "name": "another_name",
        "description": "A suite with a meaningful description",
        "tags": ["important", "a_second_tag", "a_third_tag"],
        "properties": {"type": "acceptance"},
        "links": [
            ("http://bugtracker.example.com/issues/1234", "TICKET-1234"),
            "http://bugtracker.example.com/issues/1235"
        ]
    }

    @lcc.test()
    def my_test():
        check_that("value", "foo", equal_to("foo"))

As it can be seen in the previous examples, test and suites name are determined from the decorated object's name or
from the current module.
It can be overridden in ``@lcc.test()`` and ``@lcc.suite()`` decorators:

.. code-block:: python

    @lcc.test(name="test_something")
    def my_test():
        pass

.. note::
    Test/suite descriptions are optional and automatically generated from the test/suite name.
    Since names are somewhat technical, it is recommended to set an explicit description to the test/suite in order
    to provide a meaningful insight of what the test/suite does to the test report reader.

Disabling a test or a suite
---------------------------

A test or an entire suite can be disabled using the ``@lcc.disabled()`` decorator::

    @lcc.test("Test something")
    @lcc.disabled()
    def test_something(self):
        pass

Disabled tests are visible in the report but they are not taken into account while computing the percentage
of successful tests.

.. versionadded:: 1.1.0
    it's possible to pass a ``reason`` (str) argument to the decorator, it will be visible in the generated report.

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


Suites discovery
----------------

Here is how suites are discovered by lemoncheesecake (by order of priority):

- if a ``$LCC_PROJECT_FILE`` environment variable is defined, then the suites will be loaded using
  this :ref:`customized project file <project>`
- a :ref:`customized project file <project>` named ``project.py`` is searched from the current directory up to the root
  directory and is used to load suites
- a ``suites`` directory is searched from the current directory up to the root directory, if it's found then
  the suites will be loaded from that directory

In the first two cases, the project file loads (by default) suites from a ``suites`` directory present at the same
level as the project file itself.

.. versionchanged:: 1.5.0

    prior to 1.5.0, a project file (``project.py``) was mandatory; since 1.5.0, lemoncheesecake can discover tests only
    from a ``suites`` directory.
