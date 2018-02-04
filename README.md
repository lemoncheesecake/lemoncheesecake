# Introduction

lemoncheesecake is a functional/QA testing framework for Python. It provides functionalities such as test launcher,
tests organization (using hierarchical test suites, tags, properties, links), fixtures, matchers, structured reporting
data (JSON, XML, JUnit) and HTML report.

Tests are organized within suites that themselves can contain sub suites allowing the building of a complex tests
hierarchy. Every tests and suites must have a name and a description. Tags, properties (key/value pairs), links can
be associated to both tests and suites. These metadata are then available in reports and can be used for test filtering
in the lemoncheesecake CLI tool `lcc`.

One of the key features of lemoncheesecake is its reporting capabilities, providing the user with various formats
(XML, JSON, HTML, JUnit, ReportPortal, Slack) and the possibility to create his own reporting backend.

lemoncheesecake is compatible with Python 2.7, 3.3-3.6.

# Installation

lemoncheesecake can be installed through pip:
```
$ pip install lemoncheesecake
```

The following reporting backends are supported:
- console: available by default
- json: available by default
- html: available by default
- xml: available through the extra `xml`
- junit: available through the extra `junit`
- reportportal: available through the extra `reportportal`
- slack: available through the extra `slack`

Lemoncheesecake can be installed with an extra like this:
```
$ pip install lemoncheesecake[xml]
```

Multiple extras can be specified:
```
$ pip install lemoncheesecake[junit,reportportal]
```

# Configuring reporting backends

Some reporting backends require specific configuration, this is done through environment variable.

## ReportPortal

The ReportPortal (https://reportportal.io) reporting backend does real time reporting, meaning you can see the
results of your tests during test execution.

- `RP_URL`: the URL toward your ReportPortal instance, example: https://reportportal.mycompany.com (mandatory)
- `RP_AUTH_TOKEN`: the token with UUID form that is used to authenticate on ReportPortal (mandatory)
- `RP_PROJECT`: the ReportPortal project where the test result will be stored (mandatory)
- `RP_LAUNCH_NAME`: the ReportPortal launch name (default is "Test Run")
- `RP_LAUNCH_DESCRIPTION`: the ReportPortal launch description (optional)

## Slack

The Slack reporting backend sends a notification at the end of the test run to a given channel or user.

### Settings

- `SLACK_HTTP_PROXY`: HTTP proxy to use to connect to Slack (optional)
- `SLACK_AUTH_TOKEN`: authentication token to connect on Slack (mandatory, it starts with `xoxb-`)
- `SLACK_CHANNEL`: the channel or the user to send message to (mandatory, syntax: `#channel` or `@user`)
- `SLACK_MESSAGE_TEMPLATE`: the message template can contain variables using the form {var}, see below
  for available variables (mandatory)
- `SLACK_ONLY_NOTIFY_FAILURE`: if this variable is set, then the notification will only be sent on failures
  (meaning if there is one or more tests with status "failed" or "skipped")

Here are the supported variables for slack message template:
- `start_time`: the test run start time
- `end_time`: the test run end time
- `duration`: the test run duration
- `total`: the total number of tests (including disabled tests)
- `enabled`: the total number of tests (excluding disabled tests)
- `passed`: the number of passed tests
- `passed_pct`: the number of passed tests in percentage of enabled tests
- `failed`: the number of failed tests
- `failed_pct`: the number of failed tests in percentage of enabled tests
- `skipped`: the number of skipped tests
- `skipped_pct`: the number of skipped tests in percentage of enabled tests
- `disabled`: the number of disabled tests
- `disabled_pct`: the number of disabled tests in percentage of all tests

An example of `SLACK_MESSAGE_TEMPLATE`:
```
MyProduct test results: {passed}/{enabled} passed ({passed_pct})
```

### Getting an API access token

You can obtain a Slack API access token for your workspace by following the steps below:
- in your Slack Workspace, click the "Apps" section
- in the Apps page, click "Manage apps..."
- the App Directory page shows up, in this page, make a search using the keyword "bots" in the top text box "Search App Directory"
- click "Bots" app > "Add configuration"
- set Username and click "Add bot integration"
- you'll get the API access token in "Integration Settings"

NB: please note that there are several ways to get an API token to interact with a Slack Workspace. You could also create 
a new Slack App but the method described above seems to be the more easy to follow.


# How does it look ?

Like this. Here is a suite that tests a GitHub API end-point:

```python
import json
import requests

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

URL  = "https://api.github.com/orgs/lemoncheesecake"

@lcc.suite("Github tests")
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
        check_that_in(
            data,
            "type", is_("Organization"),
            "id", is_integer(),
            "description", is_not_none(),
            "login", is_(present()),
            "created_at", match_pattern("^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"),
            "has_organization_projects", is_true(),
            "followers", is_(greater_than_or_equal_to(0)),
            "following", is_(greater_than_or_equal_to(0)),
            "repos_url", ends_with("/repos"),
            "issues_url", ends_with("/issues"),
            "events_url", ends_with("/events"),
            "hooks_url", ends_with("/hooks"),
            "members_url", ends_with("/members{/member}"),
            "public_members_url", ends_with("/public_members{/member}")
        )
```

And here are the corresponding test results:

![alt text](https://github.com/lemoncheesecake/lemoncheesecake/blob/master/misc/github-testsuite.png?raw=true "test result")

# Getting started

## Creating a new test project

Before writing tests, you need to setup a lemoncheesecake project.

The command:
```
$ lcc bootstrap myproject
```

creates a new project directory "myproject" containing one file "project.py" (it contains your project settings) and a "suites" directory where you can add your test suites.

## Writing a suite

A suite can be represented either:

- as a module, each test is a function decorated with `@lcc.test`:
  ```python
  # tests/my_first_suite.py:
  import lemoncheesecake.api as lcc
  from lemoncheesecake.matching import *

  SUITE = {
      "description": "My first suite"
  }

  @lcc.test("My first test")
  def my_first_test():
      check_that("value", "foo", equal_to("foo"))
  ```
- as a class (in this case the class name must match the module name), each test is a method decorated with `@lcc.test`:
  ```python
  # tests/my_first_suite.py:
  import lemoncheesecake.api as lcc
  from lemoncheesecake.matching import *

  @lcc.suite("My first suite")
  class my_first_suite:
      @lcc.test("My first test")
      def my_first_test(self):
          check_that("value", "foo", equal_to("foo"))
  ```

The two examples above declare:
- a suite whose name is `my_first_suite` (the module/class name) and description is `My first suite`
- a test whose name is `my_first_test` (the function/method name) and description is `My first test`

About imports:
- `lemoncheesecake.api` module (aliased to lcc to be shorter) contains the lemoncheesecake test API needed to write tests
- `lemoncheesecake.matching` is imported using wildcard import to make matching operations more pleasant to read:
  ```python
  # this, is more easier to read:
  check_that("value", 1, is_integer(greater_than(0)))
  # than that:
  lcc.check_that("value", 1, lcc.is_integer(lcc.greater_than(0)))
  ```

Using the default `project.py` file, suites will be loaded from the `suites` sub directory.

## Running the tests

The command `lcc run` is in charge of running the tests, it provides several option to filter the test to be run and to set the reporting backends that will be used.
```
$ lcc run --help
usage: lcc run [-h] [--desc DESC [DESC ...]] [--tag TAG [TAG ...]]
                  [--property PROPERTY [PROPERTY ...]]
                  [--link LINK [LINK ...]] [--report-dir REPORT_DIR]
                  [--reporting REPORTING [REPORTING ...]]
                  [--enable-reporting ENABLE_REPORTING [ENABLE_REPORTING ...]]
                  [--disable-reporting DISABLE_REPORTING [DISABLE_REPORTING ...]]
                  [path [path ...]]

optional arguments:
  -h, --help            show this help message and exit

Filtering:
  path                  Filter on test/suite path (wildcard character '*'
                        can be used)
  --desc DESC [DESC ...]
                        Filter on descriptions
  --tag TAG [TAG ...], -a TAG [TAG ...]
                        Filter on tags
  --property PROPERTY [PROPERTY ...], -m PROPERTY [PROPERTY ...]
                        Filter on properties
  --link LINK [LINK ...], -l LINK [LINK ...]
                        Filter on links (names and URLs)

Reporting:
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
$ lcc run
============================= my_first_suite ==============================
 OK  1 # some_test                

Statistics :
 * Duration: 0s
 * Tests: 1
 * Successes: 1 (100%)
 * Failures: 0

```

The generated HTML report is available in the file "report/report.html":

# Writing tests

lemoncheesecake provides several API functions to check data and to set various information into the test report.

## Matchers

Lemoncheesecake comes with support of matchers, a functionality inspired by [Hamcrest](http://hamcrest.org/) / [PyHamcrest](https://github.com/hamcrest/PyHamcrest).

The following stock matchers are available:

- Values:
  - `equal_to(expected)`: check if actual `==` expected
  - `not_equal_to(expected)`: check if actual `!=` expected
  - `greater_than(expected)`: check if actual `>` expected
  - `greater_than_or_equal_to(expected)`: check if actual `>=` expected
  - `less_than(expected)`: check if actual `<` expected
  - `less_than_or_equal_to(expected)`: check if actual `<=` expected
  - `is_between(min, max)`: check if actual is between min and max
  - `is_none()`: check if actual `== None`
  - `is_not_none()`: check if actual `!= None`
  - `has_length(expected)`: check if value has expected length (expected can be a value or a Matcher object)
  - `is_true()`: check if value is a boolean true
  - `is_false()`: check if value is a boolean false
- Character strings:
  - `starts_with(expected)`: check if actual string starts with expected
  - `ends_with(expected)`: check if actual string ends with expected
  - `match_pattern(expected)`: check if actual match expected regexp (expected can be a raw string or an object returned by `re.compile()`)
- Types (expected is a value or a Matcher object):
  - `is_integer(expected)`: check if actual is of type  `int`
  - `is_float(expected)`: check if actual is of type `float`
  - `is_str(expected)`: check if actual is of type `str` (or `unicode` if Python 2.7)
  - `is_dict(expected)`: check if actual is of type `dict`
  - `is_list(expected)`: check if actual is of type `list` or `tuple`
  - `is_bool(expected)`: check if actual is of type `bool`
- Iterable:
  - `has_item(expected)`: check is actual iterable has an element that matches expected (expected can be a value or a Matcher)
  - `has_values(expected)`: check is actual iterable contains **at least** the expected values
  - `has_only_values(expected)`: check if actual iterable **only contains** the expected values
  - `is_in(expected)`: check if actual value **is among** the expected values
- Dict:
  - `has_entry(expected_key [,expected_value])`: check if actual dict has `expected_key` and (optionally) the expected associated value `expected_value` (`expected_value` can be a value or a matcher)
- Logical:
  - `is_(expected)`: return the matcher if `expected` is a matcher, otherwise wraps `expected` in the `equal_to` matcher
  - `is_not(expected)`: make the negation of the `expected` matcher (or `equal_to` in the argument is not a matcher)
  - `all_of(matcher1, [matcher2, [...]])`: check if all the matchers succeed (logical **AND** between all the matchers)
  - `any_of(matcher1, [matcher2, [...]])`: check if any of the matchers succeed (logical **OR** between all the matchers)
  - `anything()`, `something()`, `existing()`: these matchers always succeed whatever the actual value is (only the matcher description changes to fit the matcher's name)


 Those matcher are used by a matching function:
 - `check_that(hint, actual, matcher, quiet=False)`: run the matcher, log the result and return the matching result as a boolean
 - `require_that(hint, actual, matcher, quiet=False)`: run the matcher, log the result and raise an `AbortTest` exception in case of match failure
 - `assert_that(hint, actual, matcher, quiet=False)`: run the match, in case of match failure log the result and raise an `AbortTest` exception

The `quiet` flag can be set to `True` to hide the matching result details in the report.

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

`check_that_entry` can also be used with the context manager `this_dict`:
```python
with this_dict({"foo": 1, "bar": 2}):
    check_that_entry("foo", equal_to(1))
    check_that_entry("bar", equal_to(2))
```

`check_that_in` can conveniently be used instead of `this_dict` + `check_that_entry` when the context manager block
only contains `check_that_entry` function calls:
```python
check_that_in(
    {"foo": 1, "bar": 2},
    "foo", equal_to(1),
    "bar", equal_to(2)
)
```

The same dict helper counter parts are available for `require_that` and `assert_that`:
- `require_that_entry` and `require_that_in`
- `assert_that_entry` and `assert_that_in`

If one match fails in a test, this test will be marked as failed.

## Logs and steps

lemoncheesecake provides logging functions that give the user the ability to log information beyond the check functions:

- `log_debug(msg)`
- `log_info(msg)`
- `log_warn(msg)`
- `log_error(msg)`: this log will mark the test as failed
- `log_url(url[, description])`

Examples:
```python
lcc.log_debug("Some debug message")
lcc.log_info("More important, informational message")
lcc.log_warning("Something looks abnormal")
lcc.log_error("Something bad happened")
lcc.log_url("http://example.com", "Example dot com")
```

Steps provide a way to organize your checks within logical steps:
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

The file will be copied into the report dir and is prefixed by a unique value, making it possible to save multiple times an attachment with the same base file name. The attachment description is optional.

There are other ways to save attachment files depending on your needs.

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
import requests
import lemoncheesecake.api as lcc

@lcc.fixture(scope="session")
def user_auth(cli_args):
    # we assume that custom cli arguments "user" and "password" have been
    # previously set through project file
    return cli_args.user, cli_args.password

@lcc.fixture(scope="session")
def api(user_auth):
    session = requests.Session()
    session.auth = user_auth
    return session

# tests/my_suite.py:
import lemoncheesecake.api as lcc

SUITE = {
    "description": "My Suite"
}

@lcc.test("Some test")
def some_test(api):
    resp = api.get("GET", "/some/resource")
    [...]
```

Fixtures can be injected into suites through parameters passed to `setup_suite` and class instance / module attributes:
```python
# tests/my_suite.py:
import lemoncheesecake.api as lcc

SUITE = {
    "description": "My Suite"
}

def setup_suite(api):
    [...]
```
```python
# tests/my_suite.py:
import lemoncheesecake.api as lcc

SUITE = {
    "description": "My Suite"
}

api = lcc.inject_fixture()
```

Fixtures with scope `session_prerun` that have been previously executed through a dependency can get be retrieved using
`lcc.get_fixture(name)`.


Four fixture scopes are available (higher to lower scope):
- `session_prerun`: fixtures with this scope will be called before the test session is started, meaning that the fixture cannot use any of the `log_*`, `check_*`, etc... functions. If a fixture with this scope raises an exception, it will prevent the tests to be executed. This behavior can be used in conjunction with the `UserError` exception and the `cli_args` fixture to handle bad CLI arguments
- `session`: fixtures with this scope are initialized at the global level
- `suite`: fixtures with this scope are initialized at the test suite level; if a suite "A" uses a `suite` scoped fixture (through a test for example), and a sub suite "B" uses the same fixture, then the fixture is initialized two times: one time for "A" and the other time for "B"
- `test`: fixtures with this scope are initialized at the test level

Please note that:
- a fixture can be called through multiple names specified in the `names` parameter (otherwise the fixture name is the fixture function name):
  ```python
  @lcc.fixture(names=("fixt_a", "fixt_b"))
  def fixt():
      [...]
  ```
- fixture teardown can be implemented using yield to initially return the fixture value and then to de-initialize the fixture:
  ```python
  @lcc.fixture()
  def resource_file():
      fh = open("/some/file", "r")
      yield fh
      fh.close()
  ```
- a fixture can use other fixtures as arguments, in this case the scope level compatibility must be respected: for example, a `test` scoped fixture can use a `session` scoped fixture, but the opposite is not true

Lemoncheesecake provides several special builtin fixtures:
- `cli_args` (`session_prerun`) is the object returned by `parse_args` of the `argparse` module that contains the actual CLI arguments; this fixture can be used to access custom command line arguments previously setup by the function by `CLI_EXTRA_ARGS` in the lemoncheesecake project file
- `project_dir` (`session_prerun`) is the path of the project, meaning the directory of the project file
- `fixture_name` is the name of the called fixture and can only be used by a fixture. A typical use case is a fixture with multiple names, `fixture_name` can be used to identify through which name the fixture has been called and adapt its behavior accordingly

Using the default `project.py` file, fixtures will be loaded from the `fixtures` sub directory.

# Test suites hierarchy

Sub test suites can be declared inside a test suite in a lot of different ways:

- as classes in a suite module:
  ```python
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
  ```
- as nested class:
  ```python
  @lcc.suite("Parent suite")
  class parent_suite:
      @lcc.suite("Child suite")
      class child_suite:
          pass
  ```
- as module in a sub directory whose name matches the parent suite module:
  ```shell
  $ tree
  .
  ├── parent_suite
  │   └── child_suite.py
  └── parent_suite.py

  1 directory, 2 files
  ```

# Test suite setup and teardown methods

Test suites provide several methods that give the user the possibility to execute code at particular steps of the suite execution:

- `setup_suite` is called before executing the tests of the suite; if something wrong happens (a call to `log_error` or a raised exception) then the whole suite execution is aborted
- `setup_test` takes the test name as argument and is called before each test; if something wrong happen then the test execution is aborted
- `teardown_test` is called after each test (it takes the test name as argument); if something wrong happens the executed test will be mark as failed
- `teardown_suite` is called after executing the tests of the suite

Note that:

- code within `setup_suite` and `teardown_suite` methods is executed in a dedicated context and the data it generates (checks, logs) will be represented the same way as a test in the test report
- code within `setup_test` and `teardown_test` methods is executed within the related test context and the data it generates will be associated to the given test

# Metadata

Various metadata can be associated to both tests and suites:

- tags (takes one or more tag name as argument):
  ```python
  @lcc.test("Test something")
  @lcc.tags("important")
  def test_something(self):
      [...]

  @lcc.test("Test something else")
  @lcc.tags("slow")
  def test_something_else(self):
      [...]

  @lcc.test("Test something else again")
  @lcc.tags("slow", "deprecated")
  def test_something_else_again(self):
      [...]
  ```
- properties (takes a name/value pair):
  ```python
  @lcc.test("Test something")
  @lcc.prop("type", "acceptance")
  def test_something(self):
      [...]

  @lcc.test("Test something else")
  @lcc.prop("type", "destructive")
  def test_something_else(self):
      [...]
  ```
- links (takes an URL and an optional description):
  ```python
  @lcc.test("Test something")
  @lcc.link("http://my.bug.tracker/issue/1234", "TICKET-1234")
  def test_something(self):
      [...]

  @lcc.test("Test something else")
  @lcc.link("http://my.bug.tracker/issue/5678")
  def test_something_else(self):
      [...]
  ```

Metadata can also be associated to a suite module using the SUITE dictionnary:

```python
SUITE = {
    "description": "My Suite",
    "tags": "slow"
}
[...]
```

Once, the metadata are set, they:

- can be used to filter the tests to be run (see the `--tag`, `--property` and `--link` of the CLI launcher), in this case a test inherits all these parents metadata
- will be available in the test report

## Disabling a test or a suite

A test or an entire suite can be disabled using the `@lcc.disabled()` decorator:

```python
@lcc.test("Test something")
@lcc.disabled()
def test_something(self):
    [...]
```

Disabled tests are visible in the report but they are not taken into account while computing the percentage of successful tests.

If you want to completely hide a test / suite from the test tree and report, use `lcc.hidden()`.

## Conditional tests and suites

A test or an entire suite can included or excluded from the test tree using the `@lcc.conditional(condition)` decorator. This decorator can be associated to both tests and suites,
it takes a callback as argument and this callback takes itself the associated instance to which it is associated. If the callback return a non-true value, then the test/suite won't be
included in the test tree, meaning it won't be executed, it won't present in the test report nor in the `lcc show` command output.

Usage:
```python
@lcc.suite("My Suite")
class mysuite:
    some_feature_enabled = True

    @lcc.test("Test something")
    @lcc.conditional(lambda test: mysuite.some_feature_enabled)
    def test_something(self):
        [...]
```


# Advanced project features

## Custom command line arguments

Custom command line arguments are can be added to `lcc run`:

```python
 # project.py:

import os.path

from lemoncheesecake.project import SimpleProjectConfiguration, HasCustomCliArgs


class MyProjectConfiguration(SimpleProjectConfiguration, HasCustomCliArgs):
    def add_custom_cli_args(self, cli_parser):
        cli_parser.add_argument("--host", required=True, help="Target host")
        cli_parser.add_argument("--port", type=int, default=443, help="Target port")


project_dir = os.path.dirname(__file__)
project = MyProjectConfiguration(
    suites_dir=os.path.join(project_dir, "suites"),
    fixtures_dir=os.path.join(project_dir, "fixtures"),
)
```

And then accessed through the `cli_args` fixture:
```python
# fixtures/fixtures.py:
def target_url(cli_args):
    return "https://%s:%s" % (cli_args.host, cli_args.port)
```

`cli_parser` is an `ArgumentParser` instance of the `argparse` module.

## Metadata Policy

The project settings provides a metadata policy that can be used to add constraints to tests and suites concerning the usage of metadata.

The following example requires that every tests provide a property "priority" whose value is among "low", "medium" and "high":

```python
 # project.py:
 
import os.path

from lemoncheesecake.project import SimpleProjectConfiguration, HasMetadataPolicy
from lemoncheesecake.validators import MetadataPolicy


class MyProjectConfiguration(SimpleProjectConfiguration, HasMetadataPolicy):
    def get_metadata_policy(self):
        policy = MetadataPolicy()
        policy.add_property_rule(
            "priority", ("low", "medium", "high"), required=True
        )
        return policy


project_dir = os.path.dirname(__file__)
project = MyProjectConfiguration(
    suites_dir=os.path.join(project_dir, "suites"),
    fixtures_dir=os.path.join(project_dir, "fixtures")
)
```

In this other example set, the metadata policy makes two tags available ("todo" and "known_defect") for both tests and suites while forbidding the usage of any other tag:

```python
 # project.py:
[...]
class MyProjectConfiguration(SimpleProjectConfiguration, HasMetadataPolicy):
    def get_metadata_policy(self):
        policy = MetadataPolicy()
        policy.add_tag_rule(
            ("todo", "known_defect"), on_test=True, on_suite=True
        )
        policy.disallow_unknown_tags()
        return policy
[...]
```

See `lemoncheesecake.validators.MetadataPolicy` for more information.

# Using lcc

## lcc commands

In addition to the main sub command `run`, the `lcc` command provides other sub commands that display various information about the test hierarchy:

- Show the tests hierarchy with metadata:
  ```
  $ lcc show
  * suite_1:
      - suite_1.test_1 (slow, priority:low)
      - suite_1.test_2 (priority:low)
      - suite_1.test_3 (priority:medium, #1235)
      - suite_1.test_4 (priority:low)
      - suite_1.test_5 (priority:high)
      - suite_1.test_6 (slow, priority:high)
      - suite_1.test_7 (priority:high)
      - suite_1.test_8 (priority:medium)
      - suite_1.test_9 (priority:medium)
  * suite_2:
      - suite_2.test_1 (priority:low)
      - suite_2.test_2 (priority:low)
      - suite_2.test_3 (priority:high)
      - suite_2.test_4 (priority:medium)
      - suite_2.test_5 (priority:low)
      - suite_2.test_6 (priority:low)
      - suite_2.test_7 (priority:medium)
      - suite_2.test_8 (slow, priority:low, #1234)
      - suite_2.test_9 (slow, priority:medium)
  ```
- Compare two reports:
  ```
  $ lcc diff report-1/ report-2/
  Added tests (1):
  - suite_3.test_1 (passed)

  Removed tests (1):
  - suite_1.test_9 (failed)

  Status changed (2):
  - suite_2.test_3 (failed => passed)
  - suite_2.test_4 (passed => failed)
  ```
- Show available fixtures:
  ```
  $ lcc fixtures

  Fixture with scope session_prerun:
  +---------+--------------+------------------+---------------+
  | Fixture | Dependencies | Used by fixtures | Used by tests |
  +---------+--------------+------------------+---------------+
  | fixt_1  | -            | 1                | 1             |
  +---------+--------------+------------------+---------------+


  Fixture with scope session:
  +---------+--------------+------------------+---------------+
  | Fixture | Dependencies | Used by fixtures | Used by tests |
  +---------+--------------+------------------+---------------+
  | fixt_2  | fixt_1       | 1                | 2             |
  | fixt_3  | -            | 2                | 1             |
  +---------+--------------+------------------+---------------+


  Fixture with scope suite:
  +---------+--------------+------------------+---------------+
  | Fixture | Dependencies | Used by fixtures | Used by tests |
  +---------+--------------+------------------+---------------+
  | fixt_4  | fixt_3       | 0                | 2             |
  | fixt_6  | fixt_3       | 1                | 1             |
  | fixt_5  | -            | 0                | 0             |
  +---------+--------------+------------------+---------------+


  Fixture with scope test:
  +---------+----------------+------------------+---------------+
  | Fixture | Dependencies   | Used by fixtures | Used by tests |
  +---------+----------------+------------------+---------------+
  | fixt_7  | fixt_6, fixt_2 | 0                | 2             |
  | fixt_8  | -              | 0                | 1             |
  | fixt_9  | -              | 0                | 1             |
  +---------+----------------+------------------+---------------+

  ```
- Show statistics on test hierarchy based on metadata:
  ```
  $ lcc stats
  Tags:
  +------+-------+------+
  | Tag  | Tests | In % |
  +------+-------+------+
  | slow | 4     | 22%  |
  +------+-------+------+

  Properties:
  +----------+--------+-------+------+
  | Property | Value  | Tests | In % |
  +----------+--------+-------+------+
  | priority | low    | 8     | 44%  |
  | priority | medium | 6     | 33%  |
  | priority | high   | 4     | 22%  |
  +----------+--------+-------+------+

  Links:
  +-------+-------------------------+-------+------+
  | Name  | URL                     | Tests | In % |
  +-------+-------------------------+-------+------+
  | #1234 | http://example.com/1234 | 1     |  5%  |
  | #1235 | http://example.com/1235 | 1     |  5%  |
  +-------+-------------------------+-------+------+

  Total: 18 tests in 2 suites
  ```
- Show a generated report on the console:
  ```
  $ lcc.py report report/
  =================================== suite_1 ===================================
   OK  1 # test_1
   OK  2 # test_2
   OK  3 # test_3
   OK  4 # test_4
   OK  5 # test_5
   OK  6 # test_6
   OK  7 # test_7
   OK  8 # test_8
   OK  9 # test_9
  
  =================================== suite_2 ===================================
   OK  1 # test_1
   OK  2 # test_2
   OK  3 # test_3
   OK  4 # test_4
   OK  5 # test_5
   OK  6 # test_6
   OK  7 # test_7
   OK  8 # test_8
   OK  9 # test_9
  
  Statistics :
   * Duration: 0s
   * Tests: 18
   * Successes: 18 (100%)
   * Failures: 0
  ```

Also see the `--help` of these sub commands.

## lcc filtering arguments

lcc commands offer various argument to filter tests, example:
```
$ lcc run --help
[...]
Filtering:
  path                  Filter on test/suite path (wildcard character '*' can
                        be used)
  --desc DESC [DESC ...]
                        Filter on descriptions
  --tag TAG [TAG ...], -a TAG [TAG ...]
                        Filter on tags
  --property PROPERTY [PROPERTY ...], -m PROPERTY [PROPERTY ...]
                        Filter on properties
  --link LINK [LINK ...], -l LINK [LINK ...]
                        Filter on links (names and URLs)
  --disabled            Filter on disabled tests
  --passed              Filter on passed tests (report-only filter)
  --failed              Filter on failed tests (report-only filter)
  --skipped             Filter on skipped tests (report-only filter)
  --enabled             Filter on enabled (non-disabled) tests
  --from-report ON_REPORT
                        When enabled, the filtering is based on the given
                        report
[...]
```

The `--from-report` argument is a special switch that tells lcc to use tests from the report rather than from the project to
build the actual filter. A typical application of this functionality is to re-run failed tests from a previous report:
```
$ lcc run --failed --from-report report/
```

# Contact

Bugs and improvement ideas are welcomed in tickets. A Google Groups forum is also available for discussions about
lemoncheesecake: https://groups.google.com/forum/#!forum/lemoncheesecake .
