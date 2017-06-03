# Introduction

lemoncheesecake is a lightweight functional / QA testing framework for Python. It provides functionalities such as test launcher, tests organization (through hierarchical test suites, tags, properties), fixtures, matchers, structured reporting data (JSON, XML) and HTML reports.

Tests are defined as methods in a testsuite class that can also contain sub testsuites allowing the developer to define a complex hierarchy of tests. Tests and testsuites are identified by a name and a description. Tags, properties (key/value pairs), links can be associated with both test and testsuites. These metadata can be used later by the user to filter the test he wants to run.

One of the key features of lemoncheesecake is it's reporting capabilities, providing the user with various formats (XML, JSON, HTML) and the possibility to create his own reporting backend.

lemoncheesecake is compatible with Python 2.7, 3.3-3.6 .

# How does it look ?

Like this. Here is testsuite that test a GitHub API end-point:

```python
import json
import requests

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

URL  = "https://api.github.com/orgs/lemoncheesecake"

@lcc.testsuite("Github tests")
class github:
    @lcc.test("Test Organization end-point")
    def organization(self):
        lcc.set_step("Get lemoncheesecake organization information")
        lcc.log_info("GET %s" % URL)
        resp = requests.get(URL)
        require_that("HTTP code", resp.status_code, is_(200))
        data = resp.json()
        lcc.log_info("Response\n%s" % json.dumps(data, indent=4))

        lcc.set_step("Check API response")
        with this_dict(data):
            check_that_entry("type", is_("Organization"))
            check_that_entry("id", is_integer())
            check_that_entry("description", is_none())
            check_that_entry("login", is_(existing()))
            check_that_entry("created_at", match_pattern("^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"))
            check_that_entry("has_organization_projects", is_bool(True))
            check_that_entry("followers", greater_than_or_equal_to(0))
            check_that_entry("following", greater_than_or_equal_to(0))
            check_that_entry("repos_url", ends_with("/repos"))
            check_that_entry("issues_url", ends_with("/issues"))
            check_that_entry("events_url", ends_with("/events"))
            check_that_entry("hooks_url", ends_with("/hooks"))
            check_that_entry("members_url", ends_with("/members{/member}"))
            check_that_entry("public_members_url", ends_with("/public_members{/member}"))
```

And here are the corresponding test results:

![alt text](https://github.com/lemoncheesecake/lemoncheesecake/blob/master/misc/github-testsuite.png?raw=true "test result")

# Getting started

## Creating a new test project

Before writing lemoncheesecake tests, you need to setup a lemoncheeseake project.

The command:
```
$ lcc bootstrap myproject
```

creates a new project directory "myproject" containing one file "project.py" (that represents your project settings) and a "tests" directory where you can put your testsuites.

## Writing a testsuite

A testsuite can be represented either:

- as a module, each test is a function decorated with `@lcc.test`:
  ```python
  # tests/my_first_testsuite.py:
  import lemoncheesecake.api as lcc
  from lemoncheesecake.matching import *

  TESTSUITE = {
      "description": "My first testsuite"
  }

  @lcc.test("My first test")
  def my_first_test():
      check_that("value", "foo", equal_to("foo"))
  ```
- as a class (in this case the class name must match the module name), each test is a method decorated with `@lcc.test`:
  ```python
  # tests/my_first_testsuite.py:
  import lemoncheesecake.api as lcc
  from lemoncheesecake.matching import *

  @lcc.testsuite("My first testsuite")
  class my_first_testsuite:
      @lcc.test("My first test")
      def my_first_test():
          check_that("value", "foo", equal_to("foo"))
  ```

The two examples above declare:
- a testsuite whose name is `my_first_testsuite` (the module/class name) and description is `My first testsuite`
- a test whose name is `my_first_test` (the function/method name) and description is `My first test`

The `lemoncheesecake.api` module (aliased to lcc to be more developer-friendly) contains the lemoncheesecake test API needed to write tests.

## Running the tests

The command `lcc run` is in charge of running the tests, it provides several option to filter the test to be run and to set the reporting backends that will be used.
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

The generated HTML report is available in the file "report/report.html":

# Writing tests

Lemoncheesecake provides several API functions to check data and to set various information into the test report.

## Matchers

Lemoncheesecake comes with support of matchers, a functionality inspired by [Hamcrest](http://hamcrest.org/) / [PyHamcrest](https://github.com/hamcrest/PyHamcrest).

The following stock matchers are available:

- Values:
  - `equal_to(expected)`: match using `==` operator
  - `not_equal_to(expected)`: match using `!=` operator
  - `greater_than(expected)`: match using `>` operator
  - `greater_than_or_equal_to(expected)`: match using `>=` operator
  - `less_than(expected)`: match using `<` operator
  - `less_than_or_equal_to(expected)`: match using `<=` operator
  - `is_between(min, max)`: match if actual value is between min and max
  - `is_none()`: match using `== None`
  - `is_not_none()`: match using `!= None`
  - `has_length(expected)`: match if value has expected length while expected can be a value or a Matcher object
- Character strings:
  - `starts_with(expected)`: match beginning of the string
  - `ends_with(expected)`: match end of the string
  - `match_pattern(expected)`: match using regexp (expected can be a raw string or an object returned by re.compile())
- Types (expected is a value or a Matcher object):
  - `is_integer(expected)`: match type `int`
  - `is_float(expected)`: match type `float`
  - `is_str(expected)`: match types `str` and `unicode` (Python 2.x)
  - `is_dict(expected)`: match type `dict`
  - `is_list(expected)`: match types `list` and `tuple`
- Iterable:
  - `has_item(expected)`: the iterable has an element that matches expected (value or matcher)
  - `has_values(values)`: the iterable contains (at least) the values passed as argument
  - `has_only_values(values)`: the iterable only contains the values passed as argument
  - `is_in(values)`: match if the actual value is among the given values
- Dict:
  - `has_entry(key[, value])`: match dict key and optionally match associated value (with value or Matcher object)
- Logical:
  - `is_(expected)`: return the matcher if `expected` is a matcher, otherwise wraps its value with `equal_to`
  - `is_not(expected)`: make the negation of the matcher in argument (or `equal_to` in the argument is not a matcher)
  - `all_of(matcher1, [matcher2, [...]])`: logical **AND** between all the matchers in argument
  - `any_of(matcher1, [matcher2, [...]])`: logical **OR** between all the matchers in argument
  - `anything()`, `something()`, `existing()`: those matchers always return success whatever the actual value (only the matcher description change between them)


 Those matcher are used by a matching function:
 - `check_that`: run the matcher, log the result and return the matching result as a boolean
 - `require_that`: run the matcher, log the result and raise an `AbortTest` exception in case of match failure
 - `assert_that`: run the match, in case of match failure log the result and raise an `AbortTest` exception

These matching functions take the following arguments:
- a hint that will be used to build the matcher description
- the actual value to be matched
- the matcher instance
- an optional `quiet` flag that is used to hide matching details in the report (`False` by default)

The `lemoncheesecake.matching` module also provides helper functions to ease operations on dict object:

The code:
```python
data = {"foo": 1, "bar": 2}
check_that("data", data, has_entry("foo", equal_to(1)))
check_that("data", data, has_entry("bar", equal_to(2)))
```

Can be shortened like this:
```python
data = {"foo": 1, "bar": 2}
check_that_entry("foo", equal_to(1), in_=data)
check_that_entry("bar", equal_to(2), in_=data)
```

And made even shorter (while still nicely readable) like this:
```python
with this_dict({"foo": 1, "bar": 2}):
    check_that_entry("foo", equal_to(1))
    check_that_entry("bar", equal_to(2))
```

If one match fails in a test, this test will be marked as failed.

## Logs and steps

lemoncheesecake provides logging functions that give the user the ability to log information beyond the check functions. There are four logging functions available corresponding to four logging levels:

- `log_debug`
- `log_info`
- `log_warn`
- `log_error`: this log will set the test as failed

```python
lcc.log_debug("Some debug message")
lcc.log_info("More important, informational message")
lcc.log_warn("Something looks abnormal")
lcc.log_error("Something bad happened")
```

Steps provide a way to organize your checks and logs when they tend to be quite large:
```python
lcc.set_step("Prepare stuff for test")
value = 42
lcc.log_info("Retrieve data for %d" % value)
data = some_function_that_provide_data(value)
lcc.log_info("Got data: %s" % data)

lcc.set_step("Check data")
with this_dict(data):
    check_that_entry("foo", equal_to(21))
    check_that_entry("bar", equal_to(42))
```

## Attachments

Within a test, you also have the possibility to attach files to the report:
```python
lcc.save_attachment_file(filename, "The application screenshot")
```

The file will be copied into the report dir and is prefixed by a unique value, making it possible to save multiple times an attachment with the same name. The attachment description is optional (the given filename will be used as a description).

There are other ways to save attachment files depending on your need.

If the file you want to save is loaded in memory:
```python
lcc.save_attachment_content(image_data, "screenshot.png", "The application screenshot")
```

If you need the effective file path to write into:
```python
path = lcc.prepare_attachment("screenshot.png", "The application screenshot")
with open(path, "w") as fh:
    fh.write(image_data)
```

## Fixtures

Lemoncheesecake provides a fixture system similar to what pytest offers (please refer to: http://doc.pytest.org/en/latest/fixture.html#fixture).
Fixtures are a powerful and modular way to inject dependencies into your tests.

```python
# fixtures/myfixtures.py:
import lemoncheesecake.api as lcc
import httplib

@lcc.fixture(scope="session")
def conn():
    return httplib.HTTPSConnection("www.someonlineapi.io")

# tests/my_suite.py:
import lemoncheesecake.api as lcc

TESTSUITE = {
    "description": "My Suite"
}

@lcc.test("Some test")
def some_test(self, conn):
    conn.request("GET", "/some/resource")
    resp =  conn.getresponse()
```

Four fixture scopes are available (higher to lower scope):
- `session_prerun`: fixtures with this scope will be called before the test session is started, meaning that the fixture cannot use any of the `log_*`, `check_*`, etc... functions; this scope can be very handy because exception happening on a fixtures using this scope will prevent test session to start
- `session`: fixtures with this scope are initialized at the global level
- `testsuite`: fixtures with this scope are initialized at the test suite level; if a testsuite "A" uses a `testsuite` scoped fixture (through a test for example), and a sub testsuite "B" uses the same fixture, then the fixture is initialized two times: one time for "A" and the other time for "B"
- `test`: fixtures with this scope are initialized at the test level

Please note that:
- a fixture can be called through multiple names specified in the `names` parameter (otherwise the fixture name is fixture function name):
```python
@lcc.fixture(names=("fixt_a", "fixt_b"))
def fixt():
    [...]
```
- fixture teardown can be implemented using yield to initially return the fixture value and then to de-initialize the fixture
- a fixture can use fixtures as parameters
- when a fixture uses an other fixture, the scope level compatibility must be respected: for example, a `test` scoped fixture can use a `session` scoped fixture, but the opposite is not true

Lemoncheesecake provides several special builtin fixtures:
- `cli_args` is the object returned by `parse_args` of the `argparse` module that contains the actual CLI arguments; this fixture can be used to access custom command line arguments previously setup by the function by `CLI_EXTRA_ARGS` in the lemoncheesecake project file
- `project_dir` is the path of the project, meaning the directory of the project file
- `fixture_name` is the name of the called fixture (it can be used for example if the fixture has several names and the fixture behavior changes depending on the name with which it is called)

Using the default project.py file, fixtures will be loaded from the "fixtures/" sub directory.

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
```python
 # tests/my_suite.py:
[...]

def some_test():
    worker = lcc.get_worker("myworker")
    myworker.do_some_operation(42)
```

The Worker class provides three hooks detailed in the API documentation:

- `cli_initialize`
- `setup_test_session`
- `teardown_test_session`

# Testsuites hierarchy

Sub testsuites can be declared in a testsuite in a lot of different ways:

- as classes in a testsuite module:
  ```python
  TESTSUITE = {
    "description": "Parent suite"
  }

  @lcc.test("Test A")
  def test_a():
      pass

  @lcc.testsuite("Child suite 1")
  class child_suite_1:
      @lcc.test("Test B")
      def test_b(self):
          pass

  @lcc.testsuite("Child suite 2")
  class child_suite_2:
      @lcc.test("Test C")
      def test_c(self):
          pass
  ```
- as nested class:
  ```python
  @lcc.testsuite("Parent suite")
  class parent_suite:
      @lcc.testsuite("Child suite")
      class child_suite:
          pass
  ```
- as module in a sub directory whose name matches the parent testsuite module:
  ```shell
  $ tree
  .
  ├── parent_suite
  │   └── child_suite.py
  └── parent_suite.py

  1 directory, 2 files
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

Various metadata can be associated to tests:

- tags: they are simple keywords used to tag tests or testsuites that have a particular characteristic:
  ```python
  @lcc.test("Test something")
  @lcc.tags("important")
  def test_something(self):
      pass

  @lcc.test("Test something else")
  @lcc.tags("slow")
  def test_something_else(self):
      pass

  @lcc.test("Test something else again")
  @lcc.tags("slow", "deprecated")
  def test_something_else_again(self):
      pass
  ```
- properties: they are used for keywords that have a (closed) choice of values:
  ```python
  @lcc.test("Test something")
  @lcc.prop("type", "acceptance")
  def test_something(self):
      pass

  @lcc.test("Test something else")
  @lcc.prop("type", "destructive")
  def test_something_else(self):
      pass
  ```
- links: they are used to associate a link (with an optional label) to a given test or testsuite:
  ```python
  @lcc.test("Test something")
  @lcc.link("http://my.bug.tracker/issue/1234", "TICKET-1234")
  def test_something(self):
      pass

  @lcc.test("Test something else")
  @lcc.link("http://my.bug.tracker/issue/5678")
  def test_something_else(self):
      pass
  ```

These decorators can also be applied to testsuite classes:

```python
@lcc.testsuite("My Suite")
@lcc.tags("slow")
class mysuite:
    [...]
```

Metadata can also be associated to a testsuite module using the TESTSUITE dictionnary:

```python
TESTSUITE = {
    "description": "My Suite",
    "tags": "slow"
}
[...]
```


Once, the metadata are set, they:

- can be used to filter the tests to be run (see the `--tag`, `--property` and `--link` of the CLI launcher), in this case a test inherits all these parents metadata
- will be available in the test report

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

`cli_parser` is an ArgumentParser instance of the argparse module.

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
