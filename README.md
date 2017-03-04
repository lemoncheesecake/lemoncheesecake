# Introduction

lemoncheesecake is a lightweight functional testing framework for Python. It provides functionalities such as test launcher, tests organization (through hierarchical test suites, tags, properties), structured reporting data (JSON, XML) and HTML reports.

Tests are defined as methods in a testsuite class that can also contain sub testsuites allowing the developer to define a complex hierarchy of tests. Tests and testsuites are identified by a name and a description. Tags, properties (key/value pairs), URLs can be associated with both test and testsuites. These metadata can be used later by the user to filter the test he wants to run.

One of the key features of lemoncheesecake is it's reporting capabilities, providing the user with various formats (XML, JSON, HTML) and the possibility to create his own reporting backend.

# Getting started

## Creating a new test project

Before writing lemoncheesecake tests, you need to setup a lemoncheeseake project.

The command:
```
$ lcc bootstrap myproject
```

creates a new project directory "myproject" containing one file "project.py" (that represents your project settings) and a "tests" directory where you can put your testsuites.

## Writing a testsuite

A lemoncheesecake testsuite is a class a decorated with `@testsuite` and contains tests and/or sub testsuites:
```python
 # tests/my_first_testsuite.py file:
from lemoncheesecake import *

@testsuite("My first testsuite")
class my_first_testsuite:
    @test("Some test")
    def some_test(self):
        check_str_eq("value", "foo", "foo")
```

The code above declares:

- a testsuite whose name is `my_first_testsuite` (the suite's name and description can be set through the `name` and `description` attributes of the testsuite class, otherwise they will be set to the class name)
- a test whose id is `some_test` and description is `Some test`

All lemoncheesecake functions and classes used in test modules can be imported safely through a wild import of the `lemoncheesecake` package (like in the example above).

## Running the tests

The command lcc run is in charge of running the tests, it provides several option to filter the test to be run and to set the reporting backends that will be used.
```
usage: lcc run [-h] [--desc DESC [DESC ...]] [--tag TAG [TAG ...]]
               [--property PROPERTY [PROPERTY ...]]
               [--link LINK [LINK ...]] [--report-dir REPORT_DIR]
               [--reporting REPORTING [REPORTING ...]]
               [--enable-reporting ENABLE_REPORTING [ENABLE_REPORTING ...]]
               [--disable-reporting DISABLE_REPORTING [DISABLE_REPORTING ...]]
               [--show-stacktrace]
               [path [path ...]]

positional arguments:
  path                  Filters on test/testsuite path (wildcard character '*'
                        can be used)

optional arguments:
  -h, --help            show this help message and exit
  --desc DESC [DESC ...]
                        Filters on test/testsuite descriptions
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
  --show-stacktrace     Show full stacktrace will getting an unexpected
                        exception from user code
```

Tests are run like this:
```
$ lcc run
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

## Fixtures

Lemoncheesecake provides a fixture system similar to what pytest provides (please refer to: http://doc.pytest.org/en/latest/fixture.html#fixture).
Fixtures are a powerful and modular way to inject dependencies into your tests.

```python
 # fixtures/myfixtures.py:
import httplib

@fixture(scope="session")
def conn():
    return httplib.HTTPSConnection("www.someonlineapi.io")

 # tests/my_suite.py:
from lemoncheesecake import *

@testsuite("My Suite")
class my_suite:
    @test("Some test")
    def some_test(self, conn):
        conn.request("GET", "/some/resource")
        resp =  conn.getresponse()
```

Four scopes are supported: "session_prerun", "session", "testsuite" and "test" which is the default. Like in pytest:
- fixture teardown can be implemented using yield to initially return the fixture value. 
- fixtures can be used in fixture

Lemoncheesecake provides a special builtin fixtures named **cli_args** that can be used to access custom command line arguments previous setup by the function referenced by **CLI_EXTRA_ARGS** parameter of project.py file.

Using the default project.py file, fixtures will be loaded from the fixtures/ sub directory.

## Workers

Workers are used to maintain a custom state for the user across the execution of all testsuites. It is also advised to use workers as a level of abstraction between the tests and the system under tests.

First, you need to reference your Worker in the "project.py" file:

```python
 # project.py:
[...]
class MyWorker(Worker):
    def cli_initialize(self, cli_args):
        self.config_file = cli_args.config

    def setup_test_session(self):
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

@testsuite("My Suite")
class my_suite:
    @test("Some test")
    def some_test(self):
        self.myworker.do_some_operation(42)
```

The Worker class provides three hooks detailed in the API documentation:

- `cli_initialize`
- `setup_test_session`
- `teardown_test_session`

# Testsuites hierarchy

A testsuite can also contain sub testsuites.

There are various ways to include sub testsuites in a testsuite.

By referencing it through the `sub_suite` attribute of the parent suite:
```python
@testsuite("My sub testsuite")
class my_sub_testsuite:
    pass

@testsuite("my main testsuite")
class my_main_testsuite:
    sub_suites = [my_sub_testsuite]
```

Through a nested class:
```python
@testsuite("my main testsuite")
class my_main_testsuite:
    @testsuite("My sub testsuite")
    class my_sub_testsuite:
        pass
```

When using `import_testsuites_*` functions, sub testsuites will be searched within a directory named from the parent test module:
```shell
$ ls -R
my_main_testsuite	my_main_testsuite.py

./my_main_testsuite:
my_sub_testsuite.py
```

# Testsuite setup and teardown methods

Testsuites provide several methods that give the user the possibility to execute code at particular steps of the testsuite execution:

- `setup_suite` is called before executing the tests of the testsuite; if something wrong happens (a call to `log_error` or a raised exception) then the whole testsuite execution is aborted
- `setup_test` takes the test name as argument and is called before each test; if something wrong happen then the test execution is aborted
- `teardown_test` is called after each test (it takes the test name as argument); if something wrong happens the executed test will be mark as failed
- `teardown_suite` is called after executing the tests of the testsuite

Note that:

- code within `setup_suite` and `teardown_suite` methods is executed in a dedicated context and the data it generates (checks, logs) will be represented the same way as a test in the test report
- code within `setup_test` and `teardown_test` methods is executed within the related test context and the data it generates will be associated to the given test

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

@testsuite("Movies")
class movies:
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

# Advanced features

## Custom command line arguments

Custom command line arguments are can be added to lcc-run:

```python
 # project.py:

[...]
def add_cli_args(cli_parser):
    cli_parser.add_argument("--host", required=True, help="Target host")
    cli_parser.add_argument("--port", type=int, default=443, help="Target port")
CLI_EXTRA_ARGS = add_cli_args
[...]
```

**cli_parser** is an ArgumentParser instance of the argparse module.

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

# Contact

Bugs and improvement ideas are welcomed in tickets. A Google Groups is also available for discussions about lemoncheesecake: https://groups.google.com/forum/#!forum/lemoncheesecake .
