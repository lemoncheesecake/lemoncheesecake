.. _parametrized:

Parametrized tests
==================

.. versionadded:: 1.4.0

Passing parameters as dicts
---------------------------

lemoncheesecake allows a same test to be run against a list of parameters:

.. code-block:: python

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *


    @lcc.suite()
    class suite:
        @lcc.test()
        @lcc.parametrized((
            {"phrase": "i like cakes", "word": "cakes"},
            {"phrase": "cakes with lemon are great", "word": "lemon"}
        ))
        def test(self, phrase, word):
            check_that("phrase", phrase, contains_string(word))

Parametrized tests are evaluated at project load time and lcc commands will see them as multiple, independent tests:

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
    PASSED: Test #1
    (suite.test_1)
    +----------+----------------------------------+--------------------+
    |          | Test #1                          | 0.000s             |
    +----------+----------------------------------+--------------------+
    | CHECK OK | Expect phrase to contain "cakes" | Got "i like cakes" |
    +----------+----------------------------------+--------------------+

    PASSED: Test #2
    (suite.test_2)
    +----------+----------------------------------+----------------------------------+
    |          | Test #2                          | 0.000s                           |
    +----------+----------------------------------+----------------------------------+
    | CHECK OK | Expect phrase to contain "lemon" | Got "cakes with lemon are great" |
    +----------+----------------------------------+----------------------------------+

Passing parameters in a CSV-like mode
-------------------------------------

.. versionadded:: 1.7.0 Test parameters can also be passed in a more CSV-like mode:

.. code-block:: python

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *


    @lcc.suite()
    class suite:
        @lcc.test()
        @lcc.parametrized((
            "phrase,word",
            ("i like cakes", "cakes"),
            ("cakes with lemon are great", "lemon")
        ))
        def test(self, phrase, word):
            check_that("phrase", phrase, contains_string(word))

Customizing test's name and description using a function
--------------------------------------------------------

By default, parametrized tests are named from the original test name and description.

This behavior can be changed by using a custom naming scheme:

.. code-block:: python

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *


    def naming_scheme(name, description, parameters, idx):
        return "%s_%s" % (name, parameters["word"]), "Check if phrase contains '%s'" % parameters["word"]


    @lcc.suite()
    class suite:
        @lcc.test()
        @lcc.parametrized((
            {"phrase": "i like cakes", "word": "cakes"},
            {"phrase": "cakes with lemon are great", "word": "lemon"}),
            naming_scheme)
        def test(self, phrase, word):
            check_that("phrase", phrase, contains_string(word))


.. code-block:: console

    $ lcc show
    * suite
        - suite.test_cakes
        - suite.test_lemon
    $ lcc show -d
    * Suite
        - Check if phrase contains 'cakes'
        - Check if phrase contains 'lemon'

Customizing test's name and description using strings
-----------------------------------------------------

.. versionadded:: 1.7.0 The naming scheme can be also be written as two strings with placeholders.

.. code-block:: python

    [...]

    @lcc.test()
    @lcc.parametrized((
        {"phrase": "i like cakes", "word": "cakes"},
        {"phrase": "cakes with lemon are great", "word": "lemon"}),
        ("test_{word}", "Test {word}"))
    def test(self, phrase, word):
        check_that("phrase", phrase, contains_string(word))

Example #1: loading parameters from a CSV file
----------------------------------------------

The ``@lcc.parametrized()`` decorator provides an easy to use mechanism to pass parameters to a test function as an iterable of dicts.
Previously, they were hard-coded, but they could also be defined in an external CSV file.

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


    @lcc.suite()
    class suite:
        @lcc.test()
        @lcc.parametrized(csv.DictReader(open(os.path.join(PROJECT_DIR, "data.csv"))))
        def test(self, phrase, word):
            check_that("phrase", phrase, contains_string(word))

Example #2: loading parameters from a JSON file
-----------------------------------------------

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


    @lcc.suite()
    class suite:
        @lcc.test()
        @lcc.parametrized(json.load(open(os.path.join(PROJECT_DIR, "data.json"))))
        def test(self, phrase, word):
            check_that("phrase", phrase, contains_string(word))


.. note::
    - if you want the external data file to be any file path, then you will have to use an environment variable:

    .. code-block:: python

        @lcc.parametrized(json.load(os.environ["DATA_JSON"]))

    - both parameters and fixtures can be used in a test

    - if a parameter has the same name as a fixture, then the parameter has priority over the fixture

