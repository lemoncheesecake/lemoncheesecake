# Introduction

LemoncheeseCake aims to be a lightweight functional testing framework for Python. It provides functionalities such as a test launcher, tests organization (through hierarchical test suites, tags, properties), structured reporting data (JSON, XML) and HTML reports.

Tests are defined as methods in a testsuite class that can also contain sub testsuites allowing the developer to define a complex hierarchy of tests. Tests and testsuites are identified by a unique id and a description. Tags, properties (key/value pairs), URLs can be associated to both test and testsuites. Those metadata can be used later by the user to filter the test he wants to run.
One of the key feature of LemoncheeseCake is it's reporting capabilities, providing the user with various format (XML, JSON, HTML) and the possibility to create his own reporting backend.

# The launcher

The launcher is in charge of loading the testsuites and running the tests accordingly to the user options passed through the CLI, here is an example:

```python
from lemoncheesecake.launcher import Launcher, import_testsuites_from_directory

launcher = Launcher()
launcher.load_testsuites(import_testsuites_from_directory("tests"))
launcher.handle_cli()
```

This is how you run the test:
```
$ ./mytests.py run
============================== my_first_testsuite ======================
 OK  1 # some_test    

============================== my_second_testsuite =====================
 OK  1 # some_other_test    

Statistics :
 * Duration: 0s
 * Tests: 2
 * Successes: 2 (100%)
 * Failures: 0
```

In the launcher code example:
- TestSuite classes are imported from files in the "tests" directory using `import_testsuites_in_directory`
- these classes are loaded into the launcher using the `load_testsuites` method
- the `handle_cli` method run the tests according to the options passed by the user, the usage of the launcher script looks like this:
```
usage: mytests.py run [-h] [--test-id TEST_ID [TEST_ID ...]]
                      [--test-desc TEST_DESC [TEST_DESC ...]]
                      [--suite-id SUITE_ID [SUITE_ID ...]]
                      [--suite-desc SUITE_DESC [SUITE_DESC ...]]
                      [--tag TAG [TAG ...]]
                      [--property PROPERTY [PROPERTY ...]]
                      [--url URL [URL ...]] [--report-dir REPORT_DIR]
optional arguments:
  -h, --help            show this help message and exit
  --test-id TEST_ID [TEST_ID ...], -t TEST_ID [TEST_ID ...]
                        Filters on test IDs
  --test-desc TEST_DESC [TEST_DESC ...]
                        Filters on test descriptions
  --suite-id SUITE_ID [SUITE_ID ...], -s SUITE_ID [SUITE_ID ...]
                        Filters on test suite IDs
  --suite-desc SUITE_DESC [SUITE_DESC ...]
                        Filters on test suite descriptions
  --tag TAG [TAG ...], -a TAG [TAG ...]
                        Filters on test & test suite tags
  --property PROPERTY [PROPERTY ...], -m PROPERTY [PROPERTY ...]
                        Filters on test & test suite property
  --url URL [URL ...], -u URL [URL ...]
                        Filters on test & test suite url names
  --report-dir REPORT_DIR, -r REPORT_DIR
                        Directory where reporting data will be stored
```

Options like --test-id, --test-desc, --tag filter the test to be run based on their metadata. Available metadata will be detailed later on this document.

# The testsuite

Here is a testsuite example. The purpose of the test is to test the omdbapi Web Service API. We lookup 'The Matrix' movie and then check several elements of the returned data.
```python
import re
import urllib2
import json

from lemoncheesecake import *

class my_first_testsuite(TestSuite):
  @test("Some test")
  def some_test(self):
    set_step("Make HTTP request")
    req = urllib2.urlopen("http://www.omdbapi.com/?t=matrix&y=1999&plot=short&r=json")
    assert_eq("HTTP status code", req.code, 200)

    set_step("Check JSON response")
    content = req.read()
    log_info("Raw JSON: %s" % content)
    try:
      data = json.loads(content)
    except ValueError:
      raise AbortTest("The returned JSON is not valid")
    check_dictval_str_eq("Title", data, "The Matrix")
    check_dictval_str_contains("Actors", data, "Keanu Reeves")
    check_dictval_str_match("Director", data, re.compile(".+Wachow?ski", re.I))
    if check_dict_has_key("imdbRating", data):
      check_gt("imdbRating", float(data["imdbRating"]), 8.5)
```

All lemoncheesecake classes, functions, decorators needed in testsuites can be safely imported through a wild import of the `lemoncheesecake` package.
A testsuite module must inherit from the TestSuite class, in case you load your test classes using the `import_testsuites_in_directory` function of the launcher package, it is required that your class name has the same name as its module container. A testsuite can contains several tests and sub testsuites. The `@test` decorator takes a description as argument and make an object method a test of the testsuite. The first line of the test is a call to step that will group the following logs and checks. Each new call to the step function creates a new step at the test level. Once we have performed an http/API call using urllib2, the first thing we do is to check for HTTP code status. We use the assert_eq function for that. Each checker function is available in two forms:
- one with a `check_` prefix, it will perform the requested check, add the result in the report, and the test will continue (whatever of the outcome of test is)
- the other one with an `assert_` prefix, it behaves like check_ but stops the test (it raises an AbortTest exception) if the check fails

`assert_*` methods are used when a check failure means that the test cannot go further, like in this example: if the server does not return a successful HTTP response, there won't be any JSON data to check.

The second part of the test checks the validity of various fields returned by the API. The info function adds a log of type info. The JSON string is converted into a Python data structure, if the JSON is not valid (a ValueError is raised) we abort the test explicitly and cleanly by raising an AbortTest exception. If the ValueError was not caught, the test would have also been stopped, mark as failed and the whole stacktrace would have been logged in the report. Nevertheless, it is advised that you handle exceptions raised directly or indirectly by the system under test yourself and give them a more high level signification (see the error message passed to AbortTest), it will make your report more human readable.

The `{check,assert}_dict_value_*` functions wrap existing checker functions to lookup the value
