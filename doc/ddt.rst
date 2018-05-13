.. _ddt:

Data Driven Testing (DDT)
=========================

Unlike other frameworks, lemoncheesecake does not provide a dedicated API allowing a given test function to be run
against data defined in an external file. However, a test suite can be built programmatically making it easy to implement
data driven tests with any kind of input data.

Here is simple example where the input data is defined in a JSON file (it could have been XML, YAML, CSV, INI, plain text, etc...
JSON has been chosen because it's easy to process and demonstrate).
Each data entry defines two operands ``i`` and ``j``, ``expected`` is the result of their addition .

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

    import os.path as osp
    import json

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *

    PROJECT_DIR = osp.join(osp.dirname(__file__), "..")


    @lcc.suite("Add")
    class add:
        def __init__(self):
            data = json.load(open(osp.join(PROJECT_DIR, "data.json")))
            for entry in data:
                test = lcc.Test(
                    entry["name"], entry["description"],
                    lambda: self.test_add(entry["i"], entry["j"], entry["expected"])
                )
                lcc.add_test_into_suite(test, self)

        @staticmethod
        def test_add(i, j, expected):
            check_that("%d + %d" % (i, j), i + j, equal_to(expected))


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
