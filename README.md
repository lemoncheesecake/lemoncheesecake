# Introduction

lemoncheesecake is a lightweight functional testing framework for Python. It provides functionalities such as test launcher, tests organization (through hierarchical test suites, tags, properties), structured reporting data (JSON, XML) and HTML reports.

Tests are defined as methods in a testsuite class that can also contain sub testsuites allowing the developer to define a complex hierarchy of tests. Tests and testsuites are identified by a unique id and a description. Tags, properties (key/value pairs), URLs can be associated with both test and testsuites. These metadata can be used later by the user to filter the test he wants to run.

One of the key features of lemoncheesecake is it's reporting capabilities, providing the user with various formats (XML, JSON, HTML) and the possibility to create his own reporting backend.

# Getting started

## Creating a new test project

Before writing lemoncheesecake tests, you need to setup a lemoncheeseake project.

The command:
```
$ lcc-create-project myproject
```

creates a new project directory "myproject" containing one file "project.py" (that represents your project settings) and a "tests" directory where you can put your testsuites.

## Writing a testsuite

A lemoncheesecake testsuite is a class that inherits from `TestSuite` and contains tests and/or sub testsuites:
```python
 # tests/my_first_testsuite.py file:
from lemoncheesecake import *

class my_first_testsuite(TestSuite):
    @test("Some test")
    def some_test(self):
        check_str_eq("value", "foo", "foo")
```

The code above declares:

- a testsuite whose id is `my_first_testsuite` (the suite's id and description can be set through the `id` and `description` attributes of the testsuite class, otherwise they will be set to the class name)
- a test whose id is `some_test` and description is `Some test`

All lemoncheesecake functions and classes used in test modules can be imported safely through a wild import of the `lemoncheesecake` package (like in the example above).

## Running the tests

The command lcc-run is in charge of running the tests, it provides several option to filter the test to be run and to set the reporting backends that will be used.
```
$ lcc-run --help
usage: lcc-run    [-h] [--test-id TEST_ID [TEST_ID ...]]
                  [--test-desc TEST_DESC [TEST_DESC ...]]
                  [--suite-id SUITE_ID [SUITE_ID ...]]
                  [--suite-desc SUITE_DESC [SUITE_DESC ...]]
                  [--tag TAG [TAG ...]] [--property PROPERTY [PROPERTY ...]]
                  [--link LINK [LINK ...]] [--report-dir REPORT_DIR]
                  [--reporting REPORTING [REPORTING ...]]
                  [--enable-reporting ENABLE_REPORTING [ENABLE_REPORTING ...]]
                  [--disable-reporting DISABLE_REPORTING [DISABLE_REPORTING ...]]

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
  --link LINK [LINK ...], -l LINK [LINK ...]
                        Filters on test & test suite link names
  --report-dir REPORT_DIR, -r REPORT_DIR
                        Directory where report data will be stored
  --reporting REPORTING [REPORTING ...]
                        The list of reporting backends to use
  --enable-reporting ENABLE_REPORTING [ENABLE_REPORTING ...]
                        The list of reporting backends to add (to base
                        backends)
  --disable-reporting DISABLE_REPORTING [DISABLE_REPORTING ...]
                        The list of reporting backends to remove (from base
                        backends)
```

Tests are run like this:
```
$ lcc-run
============================= my_first_testsuite ==============================
 OK  1 # some_test                

Statistics :
 * Duration: 0s
 * Tests: 1
 * Successes: 1 (100%)
 * Failures: 0

```

The generated HTML report is available in report/report.html:

![alt text](https://bytebucket.org/ndelon/lemoncheesecake/raw/5cd93fe6cc55eff146fc973a355554c67d3a25cd/misc/report-screenshot.png "Test Report")

# Writing tests

Lemoncheeseacke provides several API functions to check data and to set various information into the test report.

## Checkers

lemoncheesecake comes with a wide variety of checkers that allow you to check if values fulfill given conditions, examples:
```python
@test("Some test")
def some_test(self):
    check_eq("my value", 2 + 2, 4)
    check_str_not_eq("my string", "foobaz", "foobar")
    check_gt("other value", 5, 2)
```

Checker functions like `check_int_eq` or `check_float_gteq` also perform a check on the actual value type, meaning:
```python
check_int_eq("my value", 2.0, 2)
```
will fail, whereas:

```python
check_eq("my value", 2.0, 2)
```
will succeed.

All these checkers are also available in a dict variant (where the value to check is a dict entry) handling a possible key error:
```python
d = {"foo": 42}
check_dictval_eq("foo", d, 2)
check_dictval_int_gt("bar", d, 3) # will properly fail by indicating that "bar" is not present
```

`check_` functions return `True` if the check succeed and return `False` otherwise. All `check_` functions have their `assert_` equivalent that returns no value if the assertion succeeds and stops the test (by raising `AbortTest`) otherwise.

If one check fails in a test, this test will be marked as failed.

## Logs and steps

lemoncheesecake provides logging functions that give the user the ability to log information beyond the check functions. There are four logging functions available corresponding to four logging levels:

- `log_debug`
- `log_info`
- `log_warn`
- `log_error`: this log will set the test as failed

```python
log_debug("Some debug message")
log_info("More important, informational message")
log_warn("Something looks abnormal")
log_error("Something bad happened")
```

Steps provide a way to organize your checks and logs when they tend to be quite large:
```python
set_step("Prepare stuff for test")
value = 42
log_info("Retrieve data for %d" % value)
data = some_function_that_provide_data(value)
log_info("Got data: %s" % data)

set_step("Check data")
check_dictval_eq(data, "foo", 21)
check_dictval_eq(data, "bar", 42)
```

## Attachments

Within a test, you also have the possibility to attach files to the report:
```python
save_attachment_file(filename, "The application screenshot")
```

The file will be copied into the report dir and is prefixed by a unique value, making it possible to save multiple times an attachment with the same name. The attachment description is optional (the given filename will be used as a description).

There are other ways to save attachment files depending on your need.

If the file you want to save is loaded in memory:
```python
save_attachment_content(image_data, "screenshot.png", "The application screenshot")
```

If you need the effective file path to write into:
```python
path = prepare_attachment("screenshot.png", "The application screenshot")
with open(path, "w") as fh:
    fh.write(image_data)
```

## Workers

Workers are used to maintain a custom state for the user across the execution of all testsuites. It is also advised to use workers as a level of abstraction between the tests and the system under tests.

First, you need to reference your Worker in the "project.py" file:

```python
 # project.py:
[...]
class MyWorker(Worker):
    def cli_initialize(self, cli_args):
        self.config_file = cli_args.config

    def before_tests(self):
        self.config = do_something_with_config_file(self.config_file)

    def do_some_operation(self, some_value):
        return some_func(self.config, some_value)

WORKERS = {"myworker": MyWorker()}
[...]
```

Then, you can access and use the worker through the name you associated it to:
```
 # tests/my_suite.py:
from lemoncheesecake import *

class my_suite(TestSuite):
    @test("Some test")
    def some_test(self):
        self.myworker.do_some_operation(42)
```

The Worker class provides three hooks detailed in the API documentation:

- `cli_initialize`
- `before_tests`
- `after_tests`

# Testsuites hierarchy

A testsuite can also contain sub testsuites.

There are various ways to include sub testsuites in a testsuite.

By referencing it through the `sub_suite` attribute of the parent suite:
```python
class my_sub_testsuite(TestSuite):
    pass

class my_main_testsuite(TestSuite):
    sub_suites = [my_sub_testsuite]
```

Through a nested class:
```python
class my_main_testsuite(TestSuite):
    class my_sub_testsuite(TestSuite):
        pass
```

When using `import_testsuites_*` functions, sub testsuites will be searched within a directory named from the parent test module:
```shell
$ ls -R
my_main_testsuite	my_main_testsuite.py

./my_main_testsuite:
my_sub_testsuite.py
```

# Testsuite hooks

Testsuites provide several methods that give the user the possibility to execute code at particular steps of the testsuite execution:

- `before_suite` is called before executing the tests of the testsuite; if something wrong happens (a call to `log_error` or a raised exception) then the whole testsuite execution is aborted
- `before_test` takes the test name as argument and is called before each test; if something wrong happen then the test execution is aborted
- `after_test` is called after each test (it takes the test name as argument); if something wrong happens the executed test will be mark as failed
- `after_suite` is called after executing the tests of the testsuite

Note that:

- code within `before_suite` and `after_suite` methods is executed in a dedicated context and the data it generates (checks, logs) will be represented the same way as a test in the test report
- code within `before_test` and `after_test` methods is executed within the related test context and the data it generates will be associated to the given test

# Metadata

Various metadata can be associated to tests and testsuites:

- tags: they are simple keywords used to tag tests or testsuites that have a particular characteristic:

```python
@tags("important")
@test("Test something")
def test_something(self):
    pass

@tags("slow")
@test("Test something else")
def test_something_else(self):
    pass

@tags("slow", "deprecated")
@test("Test something else again")
def test_something_else_again(self):
    pass
```
- properties: they are used for keywords that have a (closed) choice of values:

```python
@prop("type", "acceptance")
@test("Test something")
def test_something(self):
    pass

@prop("type", "destructive")
@test("Test something else")
def test_something_else(self):
    pass
```
- links: they are used to associate a link (with an optional label) to a given test or testsuite:

```python
@link("http://my.bug.tracker/issue/1234", "TICKET-1234")
@test("Test something")
def test_something(self):
    pass

@link("http://my.bug.tracker/issue/5678")
@test("Test something else")
def test_something_else(self):
    pass
```

These metadata:

- can be used to filter the tests to be run (see the `--tag`, `--property` and `--link` of the CLI launcher)
- will be available in the test report

## Metadata Policy

The project settings provides a metadata policy that can be used to add constraints to metadata.

For example, for the usage of a property "priority" on all tests with a given set of values:

```python
 # project.py:
[...]
mp = validators.MetadataPolicy()
mp.add_property_rule(
    "priority", ("low", "medium", "high")), required=True
)
METADATA_POLICY = mp
[...]
```

Add a limited set of tags available for both tests and testsuites and forbid the usage of any other tags:

```python

 # project.py:
[...]
mp = validators.MetadataPolicy()
mp.add_tag_rule(
    ("todo", "known_defect"), on_test=True, on_suite=True
)
mp.disallow_unknown_tags()
METADATA_POLICY = mp
```

See `lemoncheesecake.validators.MetadataPolicy` for more information.

# Put it all together

Here is a project/testsuite example. The purpose of the test is to test the omdbapi Web Service API. We lookup 'The Matrix' movie and then check several elements of the returned data.
```python
 # project.py:
[...]
import urllib
import urllib2
import json

class OmdbapiWorker(Worker):
    def __init__(self):
        self.host = "www.omdbapi.com"

    def get_movie_info(self, movie, year):
        set_step("Make HTTP request")
        req = urllib2.urlopen("http://{host}/?t={movie}&y={year}&plot=short&r=json".format(
            host=self.host, movie=urllib.quote(movie), year=int(year)
        ))
        assert_eq("HTTP status code", req.code, 200)

        content = req.read()
        log_info("Response body: %s" % content)
        try:
            return json.loads(content)
        except ValueError:
            raise AbortTest("The returned JSON is not valid")

WORKERS = {"omdb": OmdbapiWorker()}
[...]

 # tests/movies.py
from lemoncheesecake import *

class movies(TestSuite):
	@test("Retrieve Matrix main information on omdb")
	def test_matrix(self):
		data = self.omdb.get_movie_info("matrix", 1999)
		set_step("Check movie information")
		check_dictval_str_eq("Title", data, "The Matrix")
		check_dictval_str_contains("Actors", data, "Keanu Reeves")
		check_dictval_str_match("Director", data, re.compile(".+Wachow?ski", re.I))
		if check_dict_has_key("imdbRating", data):
			check_gt("imdbRating", float(data["imdbRating"]), 8.5)
```

# Contact

Bugs and improvement ideas are welcomed in tickets. A Google Groups is also available for discussions about lemoncheesecake: https://groups.google.com/forum/#!forum/lemoncheesecake .
