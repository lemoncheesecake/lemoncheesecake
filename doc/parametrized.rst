.. _parametrized:

Parametrized tests
==================

.. versionadded:: 1.4.0

lemoncheesecake allows a same test to be run against a list of parameters:

.. code-block:: python

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *


    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        @lcc.parametrized((
            {"phrase": "i like cakes", "word": "cakes"},
            {"phrase": "cakes with lemon are great", "word": "lemon"}
        ))
        def test(self, phrase, word):
            check_that("phrase", phrase, contains_string(word))

Parametrized tests are evaluated at project load time and each expanded test is seen like an individual test by lcc commands:

.. code-block:: console

    $ lcc show
    * suite
        - suite.test_1
        - suite.test_2

    $ lcc run
    ==================================== suite ====================================
     OK  1 # suite.test_1
     OK  2 # suite.test_2

    Statistics :
     * Duration: 0.003s
     * Tests: 2
     * Successes: 2 (100%)
     * Failures: 0

    $ lcc report -e
    PASSED: test #1
    (suite.test_1)
    +----------+----------------------------------+--------------------+
    |          | test #1                          | 0.000s             |
    +----------+----------------------------------+--------------------+
    | CHECK OK | Expect phrase to contain "cakes" | Got "i like cakes" |
    +----------+----------------------------------+--------------------+

    PASSED: test #2
    (suite.test_2)
    +----------+----------------------------------+----------------------------------+
    |          | test #2                          | 0.000s                           |
    +----------+----------------------------------+----------------------------------+
    | CHECK OK | Expect phrase to contain "lemon" | Got "cakes with lemon are great" |
    +----------+----------------------------------+----------------------------------+

When parametrized tests are expanded, they are named according the base test name and description as it can be seen above.

This behavior can be changed by using a custom naming scheme:

.. code-block:: python

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *


    def naming_scheme(name, description, parameters, idx):
        return "%s_%s" % (name, parameters["word"]), "Check if phrase contains '%s'" % parameters["word"]


    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        @lcc.parametrized((
            {"phrase": "i like cakes", "word": "cakes"},
            {"phrase": "cakes with lemon are great", "word": "lemon"}
        ), naming_scheme)
        def test(self, phrase, word):
            check_that("phrase", phrase, contains_string(word))


.. code-block:: console

    $ lcc show
    * suite
        - suite.test_cakes
        - suite.test_lemon
    $ lcc show -d
    * suite
        - Check if phrase contains 'cakes'
        - Check if phrase contains 'lemon'

The naming scheme is a function that takes the base test name, description, associated parameters, test number
(starting at 1) and must return a two elements list: the name and the description of the expanded test.

The ``@lcc.parametrized()`` decorator provides an easy to use mechanism to pass parameters to a test function as a list
(or more generally speaking, an iterable) of dict. In the previous example they were hard-coded, but something more
complex can be implemented such as taking parameters from an external file.

`Example for a CSV file <https://github.com/lemoncheesecake/lemoncheesecake/tree/master/examples/example12>`_
(given a ``data.csv`` file stored in the project directory):

.. code-block:: text

    phrase,word
    i like cakes,cakes
    cakes with lemon are great,lemon

.. code-block:: python

    import os.path
    import csv

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *

    PROJECT_DIR = os.path.join(os.path.dirname(__file__), "..")


    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        @lcc.parametrized(csv.DictReader(open(os.path.join(PROJECT_DIR, "data.csv"))))
        def test(self, phrase, word):
            check_that("phrase", phrase, contains_string(word))


`Another example with a JSON file <https://github.com/lemoncheesecake/lemoncheesecake/tree/master/examples/example13>`_
(given a ``data.json`` file stored in the project directory):

.. code-block:: json

    [
        {
            "phrase": "i like cakes",
            "word": "cakes"
        },
        {
            "phrase": "cakes with lemon are great",
            "word": "lemon"
        }
    ]

.. code-block:: python

    import os.path
    import json

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *

    PROJECT_DIR = os.path.join(os.path.dirname(__file__), "..")


    @lcc.suite("suite")
    class suite:
        @lcc.test("test")
        @lcc.parametrized(json.load(open(os.path.join(PROJECT_DIR, "data.json"))))
        def test(self, phrase, word):
            check_that("phrase", phrase, contains_string(word))


If you want the external data file to be any file path, then you will have to use an environment variable:

.. code-block:: python

    @lcc.parametrized(json.load(os.environ["DATA_JSON"]))


.. note::

    - both parameters and fixtures can be used in a test

    - if a parameter has the same name as a fixture, then the parameter has priority over the fixture

