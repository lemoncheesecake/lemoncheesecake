.. _generated:

Generating tests
================

lemoncheesecake provides a :ref:`parametrized tests <parametrized>` feature, that allows a single test to be run against
a list of parameters, it also provides a way to dynamically generate tests.

In the following example, tests are generated from data defined in a JSON file. Please note that in real life,
parametrized tests would be a better fit for achieving the same purpose.

Project structure:

.. code-block:: none

    $ find -type f
    ./suites/add.py
    ./project.py
    ./data.json


Input data (the ``data.json`` file):

.. code-block:: json

    [
        {
            "name": "one_plus_one",
            "description": "Add one to one",
            "i": 1,
            "j": 1,
            "expected": 2
        },
        {
            "name": "two_plus_two",
            "description": "Add two to two",
            "i": 2,
            "j": 2,
            "expected": 4
        }
    ]

The test suite module (the ``suites/add.py`` file):

.. code-block:: python

    import os.path
    import json

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *

    PROJECT_DIR = os.path.join(os.path.dirname(__file__), "..")


    @lcc.suite("Add")
    class add:
        def __init__(self):
            data = json.load(open(os.path.join(PROJECT_DIR, "data.json")))
            for entry in data:
                test = lcc.Test(
                    entry["name"], entry["description"],
                    self.make_test_func(entry["i"], entry["j"], entry["expected"])
                )
                lcc.add_test_into_suite(test, self)

        @staticmethod
        def make_test_func(i, j, expected):
            def func():
                check_that("%d + %d" % (i, j), i + j, equal_to(expected))
            return func

The test function could also be implemented as a callable object (i.e implementing the ``__call__`` method):

.. code-block:: python

    class TestAdd(object):
        def __init__(self, i, j, expected):
            self.i = i
            self.j = j
            self.expected = expected

        def __call__(self):
            check_that(
                "%d + %d" % (self.i, self.j), self.i + self.j, equal_to(self.expected)
            )


    @lcc.suite("Add")
    class add(object):
        def __init__(self):
            data = json.load(open(os.path.join(PROJECT_DIR, "data.json")))
            for entry in data:
                test = lcc.Test(
                    entry["name"], entry["description"],
                    TestAdd(entry["i"], entry["j"], entry["expected"])
                )
                lcc.add_test_into_suite(test, self)

The callable passed to ``lcc.Test`` can also take fixtures in arguments the same way as static tests.

Tests are added to the suite through ``lcc.add_test_into_suite``. The usual extra metadata (tags, properties, links)
can also be associated to the ``lcc.Test`` instance through their corresponding attributes.
Tests are generated at project load time meaning they are visible to all ``lcc`` commands like any other test:

.. code-block:: none

    $ lcc show
    * add
        - add.one_plus_one
        - add.two_plus_two


You can find this example project
`here <https://github.com/lemoncheesecake/lemoncheesecake/tree/master/examples/example7>`_.
