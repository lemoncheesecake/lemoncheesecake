# 1.8.0 (2021-01-11)

- **HTML report**:
  - add a filter to show failed tests only
  - various visual improvements
  - under the hood: upgrade to React 17.0.1 and latest versions of other dependencies
  - under the hood: refactoring

# 1.7.0 (2020-11-22)

- **API**: parametrized test improvements:
  - parameters can now also be passed in a CSV-like mode
  - add support for strings with placeholders as a naming scheme
- **CLI**: the `LCC_PROJECT_FILE` environment variable has been deprecated/renamed in favor of `LCC_PROJECT`
- **CLI**: the `LCC_PROJECT` environment variable can also be used with a directory that holds either a `project.py` file or a `suites` sub-directory
- **CLI**: `lcc run` has a new `--project/-p` argument that takes a project path
- **API**: add matcher `has_all_items()`
- **API**: Fix `has_entry` matcher exception when an item cannot be found by index like in `has_entry(("foo", 0))` with the
  actual data being `{"foo": []}`; also fixes the same use case with `{check,require,assert}_that_in` functions
- **API**: Fix `starts_with/ends_with/contains_string` matchers exception when the actual value is not a string

# 1.6.0 (2020-11-08)

- **API**: `load_report()` and `Report` are now public and documented
  (see http://docs.lemoncheesecake.io/en/latest/report.html)
- **under the hood**: minor improvements to `Report` and related classes before making them public
- Add official support for Python 3.9

# 1.5.2 (2020-07-05)

- Make fixture evaluation order more intuitive
- Fix 'lcc report -s' displaying bad statistics when filtering arguments are used (regression introduced in 1.2.1)

# 1.5.1 (2020-06-21)

- **API**: add ``load_fixtures_from_module``
- **under the hood**: add ``Report.build_message`` (refactored from Slack reporting backend)

# 1.5.0 (2020-05-10)

- The `project.py` file is now optional (and `lcc bootstrap` command deprecated)
- The `project_dir` argument for `Project` is now optional
- The `description` argument for `@lcc.test()` and `@lcc.suite()` decorators is now optional
- The `SUITE` variable in module-suite is now optional
- The `*.py` companion file for a suite-directory is now optional
- **doc**: "Writing tests" and "Project customization" chapters have been overhauled

# 1.4.8 (2020-05-03)

- Fix `setup_suite`, `teardown_suite` and fixtures being executed even if the related suites/tests are disabled (see #16)
- Fix suite's modules not properly sorted alphabetically by default
- Fix undesired symbols import while doing the wildcard import `from lemoncheesecake.matching import *`
- `any_of()` and `all_of()` matchers: make the description single line when suited
- `is_none()` matcher: improve matcher's description
- **under the hood**: refactor and add new tests on command `lcc run`

# 1.4.7 (2020-04-18)

- **lcc run**: --exit-error-on-failure also returns a non-zero exit code on any failure in a setup/teardown result (see #15)

# 1.4.6 (2020-04-14)

- **lcc run**: when the user hits Ctrl-C, every already running tests will be interrupted when/if
  the test calls a lemoncheesecake logging function
- Fix test skip reason not properly set under certain circumstances
- **under the hood**: various main code (among which `lemoncheesecake.session`) and test code refactoring

# 1.4.5 (2020-03-08)

- **API**: the `detached_step` context manager (whose purpose is to create steps in new threads) has been deprecated;
  the `set_step` function can now be used in any context (main thread or new threads)
- **API**: the `detached` argument of the `set_step` is now deprecated
- **CLI**: the `at_each_event` option of `lcc run --save-report` has been renamed into `at_each_log`
  (backward-compatibility has been preserved)
- **lcc report**: improve logged URL display
- **doc (http://docs.lemoncheesecake.io)**: add a "Deprecations" section
- **under the hood**:
  - the step handling has been totally reworked internally in order to:
    - remove special case of "detached steps"
    - improve step handling when dealing with multiple threads within the same test
    - provide a real "end of step" event
  - `lemoncheesecake.exceptions` cleanup:
    - reorganize exception handling
    - reduce the number of exception classes from 19 to 13
    - improve the naming of various exception classes

# 1.4.4 (2020-03-04)

- **ReportPortal**: enforce reportportal-client version ~= 3.0 to avoid
  upgrading to the non-compatible 4.0.0 version

# 1.4.3 (2020-02-16)

- **ReportPortal**: do not send steps and setup/teardown results to ReportPortal if they are empty
- Fix logging in a new thread when no explicit step has been set
- **under the hood**:
  - hold events related to step and setup/teardown in to order to avoid empty steps
    and empty results as soon as possible in the event processing chain
  - put ReportPortal reporting backend under unit tests

# 1.4.2 (2020-02-09)

- Fix exponential tests running time when dealing with very large test suites (thousands of tests)
- **under the hood**:
  - put Slack reporting backend under unit tests
  - refactor Slack reporting backend
  - refactor tests of JSON & XML reporting backends and events replay
  - in behave integration unit tests, avoid forking a behave process in order to speed-up tests and
    make test coverage work

# 1.4.1 (2020-01-19)

- In `lcc report -s` and HTML report, fix wrong success percentage with in progress tests
- **under the hood**: refactor statistics computation
- **doc & packaging**: update the lemoncheesecake's tagline for "Test Storytelling"

# 1.4.0 (2019-12-18)

- **API**: add parametrized tests feature

# 1.3.1 (2019-11-03)

- Add official support for Python 3.8
- **lcc report -s**: fix status display of in progress tests
- **under the hood**: minor code refactoring and bug fix

# 1.3.0 (2019-10-20)

- Add support for behave (BDD, http://docs.lemoncheesecake.io/en/latest/bdd.html)
- **lcc run**: `--report-dir` and `--reporting` can also be controlled respectively
  through `$LCC_REPORT_DIR` and `$LCC_REPORTING` environment variables (also applies when tests are
  run through behave)
- Drop official support for Python 3.4

# 1.2.2 (2019-09-15)

- **API**: do explicit type checking for test/suite metadata and logged information (steps,
  logs, checks, attachments, urls) in order to avoid side effects, hard to debug issues, etc...
- **lcc report**: improve broken pipe errors handling on Python 3

# 1.2.1 (2019-09-08)

- **lcc top-suites**: results coming from setup/teardown are now taken into account
- **lcc top-steps**: results coming from setup/teardown are now taken into account
- **lcc top-steps**: filtering arguments such as `--grep`, `--passed` and `--failed` are now directly
  applied to the step itself instead of the parent result
- **lcc report**: broken pipe errors (that typically raised when the command is used with `| less` being
  quit before the end of the output) are now gracefully handled
- **CLI**: the `--from-report` argument is now only available for the `lcc run` command
- **under the hood**: refactoring of:
  - JSON, XML, Junit reporting backends
  - `lcc top-*` and `lcc diff` commands
  - the `lemoncheesecake.filter` module

# 1.2.0 (2019-08-27)

- **CLI**: in filtering arguments, add a `--grep` option that takes a pattern as argument
  and that can filter any text content present in steps
- **lcc report**: when filter options are used, the command will show not only test results but
  also results from test session setup, test session teardown, suite setups and suite teardowns
  if they comply to the filter
- **lcc report**: highlight anything in steps content that match `--grep` (based on filtering
  rules)
- **lcc run**: keep disabled tests as disabled when they are candidate to skip
- **doc (http://docs.lemoncheesecake.io)**: improve the CLI page

# 1.1.0 (2019-08-18)

- **lcc run**: the `--reporting` argument can now be used with turn on/off directives of default
  backends (example: `+junit` to turn on junit or `^console` to turn off console)
- **API**: `@lcc.disabled()` now takes an optional `reason` argument that will be available
  in the generated report
- **API**: `MatchDescriptionTransformer` has been renamed into `MatcherDescriptionTransformer`
  (backward-compatibility with former naming is kept)
- **PyPI**: update the "Development Status" from "Beta" to "Production/Stable" and add some extra
  pointers to sources, documentation, and issue tracker
- **doc (http://docs.lemoncheesecake.io)**:
  - add a new section that deals with `lcc run` in depth
  - improve documentation of `{check,require,assert}_that_in` functions
  - add document for `MatcherDescriptionTransformer`

# 1.0.0 (2019-08-11)

Major release with API breaking changes, see http://docs.lemoncheesecake.io/en/latest/migrating-to-v1.html
to know to migrate from 0.22.x release.

## API

- Major overhaul of `lemoncheesecake.project`, see the migration guide for more information
- Major overhaul of the `Matcher` class, see the migration guide for more information
- Add a `is_not` alias for the `not_` matcher
- In `lemoncheesecake.matching`, the following functions have been removed:
  - `this_dict`
  - `check_that_entry`
  - `require_that_entry`
  - `assert_that_entry`
- Remove the `log_warn` alias for `log_warning`
- Remove `add_test_in_suite` and `add_tests_in_suite functions`
- Matcher renamings:
  - `has_values` => `has_items`
  - `has_only_values` => `has_only_items`
- Rename `@lcc.conditional()` decorator into `@lcc.visible_if()`
- The fixture scope `session_prerun` has been renamed into `pre_run`
- The `binary_mode` argument of the `save_attachment_content` function has been removed
  (the file opening is determined upon data argument type)

## CLI

- `lcc run`: the `--enable-reporting` and `--disable-reporting` arguments have been removed

## Report

- The `generation_time` of the report is now computed by the reporting backends
- JSON/XML: dates are now stored in plain ISO8601 format in UTC
- HTML: dates are now localized in the browser's timezone
- HTML: statistics are computed in Javascript
- HTML: the report now uses static resources instead of external resources by default

## Reporting backends

- Slack & ReportPortal: all environment variables used for configuration are now prefixed by ``LCC_``,
  example: `RP_URL` => `LCC_RP_URL`

## Documentation

- Add type annotations in major part of the public API
- Website: add a API reference chapter
- Website: add a new chapter on how to create a custom matcher

## Under the hood

- Many code refactoring, among which:
  - Make the `lemoncheesecake.filter` API more Pythonic
  - Rename `runtime` into `session`
  - Improve class and attribute naming in `lemoncheesecake.reporting.report`,
    results of setup/teardown code now have a "status" attribute, also note the `TreeLocation`
    has been renamed into `ReportLocation` and moved into that module
- Fix Python warnings
- HTML report: all "data" class names have been renamed to remove the trailing "Data" and
  all component names have been updated to add a trailing "View", example:
  - `Test` => `TestView`
  - `TestData` => `Test`

# 0.22.10 (2019-05-19)

- **lcc run**: display skipped tests as '--' instead of 'KO'

# 0.22.9 (2019-04-28)

- **Report**: provide more information about why a test has been skipped

# 0.22.8 (2019-04-14)

- **ReportPortal**: the reporting backend now supports parallelized tests
- **under the hood**: the EventManager is no longer a global instance, two event
  manager implementations now exist: AsyncEventManager and SyncEventManager
- **under the hood**: suite's start/end times, as well as checks, attachments and urls times
  are now stored in JSON and XML report data

# 0.22.7 (2019-03-11)

- Fix: make all commands that use a report (``lcc diff``, ``lcc report``, ``lcc top-*``)
  work with a report corresponding to a running test session
- Fix possible crash when a test uses a ``lcc.depends_on()`` and that the referenced test fails and is defined
  in a higher level suite

# 0.22.6 (2019-01-29)

- **lcc top-suites**: show the number of tests per suite
- **CLI**: on multiple commands, the console styling was not turned off when the output got redirected
- **CLI**: fix `lcc` crash when no command is passed (Python 3 only)

## CLI breaking changes

- the following command arguments have been dropped:
  - **lcc fixtures**: `--color`, `--verbose`
  - **lcc show**: `--no-metadata`, `--short`, `--flat-mode`, `--color`
  - **lcc stats**: `--color`
- **lcc show**: `--desc-mode` has been renamed into `--show-description`

# 0.22.5 (2019-01-27)

- **under the hood**: improve task management, make it more robust and code cleaner
- **lcc version / lcc -v**: show the Python version in use

# 0.22.4 (2019-01-15)

- Fix `lcc run --save-report at_each_failed_test` (also the default value for `--save-report`) that saves the report at
  each successful test instead of each failed test (regression introduced in 0.22.0)

# 0.22.3 (2019-01-09)

- Fix `suite_teardown` & session/suite fixtures teardown called as soon as a test fails in a suite while other tests remain to be executed (regression introduced in 0.22.2 while trying to fix teardowns not being called at all)

# 0.22.2 (2019-01-07)

- Fix fixture (with scope > test) and suite teardowns not being called in case of failed test in a suite (bug was introduced in 0.19.0)

# 0.22.1 (2019-01-06)

- **lcc report**:
  - various visualization improvements
  - add a `--explicit` argument to make some indicators understandable even without color codes
  - add a `--max-width` argument to manually control the maximum width of tables

# 0.22.0 (2019-01-04)

- **lcc report**: the command now prints a detailed view of the report, the former output style (ala `lcc run`) is now
  used when the `-s/--short` argument is passed
- **lcc run**: the `--save-report` now accepts an argument with a format `every_Ns` where `N` is the time interval at which the report will be saved on disk (example: `lcc run --save-report every_10s`)
- **CLI**: in filtering arguments (when the filter is a based on an existing report), add a `--non-passed` argument 
  which is the equivalent of `--failed --skipped`
- **lcc top-{suites,tests,steps}**: disabled tests are no longer taken into account (because it makes no sense in commands that deal with test duration) 
  and `--disabled` and `--enabled` filtering arguments have also been removed accordingly 
- **XML report**: fix an exception when an XML report is read while a link without name is present

## CLI breaking changes

- **lcc top-{suites,tests,steps}**: as indicated in the previous section, the `--disabled` and `--enabled` filtering 
  arguments have been removed
- **lcc run**: the `--save-report-at` argument has been renamed into `--save-report` and the existing (as of 0.21.0)
  associated values have been prefixed with `at_`

# 0.21.0 (2018-12-16)

- **API**: add `lcc.depends_on()` decorator which provides dependencies between tests

## API breaking changes

- **API**: the checkers API has been removed (whose implementation was lying in the `lemoncheesecake.checkers` module)

# 0.20.0 (2018-11-03)

- **lcc run**: when `--threads` is used, the Ctrl-C handling has been greatly improved, the tests in-progress are not 
  stopped, but all the pending tests won't be run
- **lcc run**: fix the suite header line not being properly displayed when the tests are run sequentially
- **lcc run**: add a `--force-disabled` CLI argument to force the execution of disabled tests and suites
- **lcc run**: the report save frequency can now be set through the `--save-report-at` CLI argument
  or `$LCC_SAVE_REPORT_AT` env variable
- **lcc run**: show the test full path by default with the console reporting backend
- **API**: fix properties being automatically called when a suite class is loaded
- **API**: add a `hide_command_line_in_report` argument in `SimpleProjectConfiguration` constructor to make it
  possible to hide the command line in the resulting report
- **API**, `match_pattern`:
  - add `description` and `mention_regexp` argument to make the matcher description customizable
  - add `make_pattern_matcher` function to easily create a new matcher function from a given pattern
- **HTML report**: tests in progress are now displayed with a (pseudo) `IN_PROGRESS` status instead of `n/a`
- **console & HTML report**: support multi-line test descriptions, suite descriptions and steps
- Add official support for Python 3.7 and drop official support for Python 3.3

# 0.19.10 (2018-10-17)

- **API**: fix buggy `all_of` and `any_of` matchers when a single instance is used multiple times on Python 3

# 0.19.9 (2018-10-17)

- **HTML report**: add a link to make the report raw data downloadable
- **API**: in `match_pattern`, fix handling of non-string values
- **API**: add support for object implementing the `__call__` method as `callback` argument in `lcc.Test`

# 0.19.8 (2018-09-30)

- **HTML report**: fix the goto-to-test feature through the anchor in the URL (it has been broken since 0.12.0 when
  the HTML report has been rewritten using React) + add a smooth scroll effect

# 0.19.7 (2018-09-28)

- **HTML report**: fix regression introduced in the previous 0.19.6 version where raw attachments are displayed
  as images and vice versa

# 0.19.6 (2018-09-27)

- **API & HTML report**: three new `lemoncheesecake.api` functions are available: `prepare_image_attachment`,
  `save_image_file` and `save_image_content` that allow to save an image as attachment in the report and to
  display the image inline in the HTML report

## API breaking changes

- **API**: the `setup_test` and `teardown_test` suite methods now take the test instance as argument instead
  of the test name
- **API**: the `teardown_test` suite method now takes a second argument that represents the status of the test "so far"

# 0.19.5 (2018-07-10)

- **cli**: fix broken `--from-report` argument handling (regression introduced in 0.19.4)

# 0.19.4 (2018-07-05)

- **reporting**: fix unordered tests in suite when test's status is disabled or skipped
- **reporting**: fix unordered top suites
- **matchers**: has_item: in matcher details, display the index of the matching element instead of the sub matcher 
  details

# 0.19.3 (2018-06-25)

- **API**: the `MatchResult` class now implements `__bool__` (and `__nonzero__`) method and then can be used in boolean operations
- **API**: the `check_that`, `require_that`, `assert_that` functions now return a `MatchResult` instance (instead of a boolean for 
  the `check_that` and no return value for the two other functions)
- **API**: the `check_that_in`, `require_that_in`, `assert_that_in` functions now return a list of matcher results
- **API**: the `has_item` matcher now returns an enhanced match result instance with `index` (of the matched item in 
  the actual list) and `item` attributes

# 0.19.2 (2018-06-15)

- **junit**: fix for multi-threads run

# 0.19.1 (2018-06-10)

- **API**: add `is_text` and `is_json` matchers
- **packaging**: add long_description for PyPI

# 0.19.0 (2018-06-03)

- Rewrite the test runner in order be able to apply parallelism to all tests and not only to tests within the same suite

# 0.18.4 (2018-06-02)

- **API**: fix circular dependency detection on fixtures
- **API**: fix `add_test_into_suite` when used with a module as argument 

# 0.18.3 (2018-05-12)

- **lcc report**: fix the duration information while tests are parallelized
- **lcc report, HTML report**: display information about cumulative duration of tests when they are parallelized

# 0.18.2 (2018-05-09)

- **HTML report**: various minor fixes and improvements related to tests parallelization

# 0.18.1 (2018-05-04)

- Replace the `orderedset` module by the Raymond Hettinger's implementation of `OrderedSet` to avoid a dependency
  to a non-pure-Python module

# 0.18.0 (2018-05-01)

- tests can now be run in parallel using `lcc run --threads N` command; please note that test suites are run
  **sequentially** and that tests within test suites are run in **parallel**, this behavior will be improved
  in future releases so that tests can be spread on different threads independently from their parent suite

## API breaking changes

- the signature of `pre_run` and `post_run` methods of `ProjectConfiguration` class in user `project.py` file
  is now `{pre_run,post_run}(self, cli_args, report_dir)` instead of `{pre_run,post_run}(self, report_dir)`,
  in other words: CLI arguments are now passed in pre and post hook methods of the project

# 0.17.2 (2018-04-15)

- **API**: in 'detached_step' context manager, handle possible exceptions in order to properly caught exceptions
  raised within a new thread
- **report**: simplify report check descriptions produced by `check_that_entry` and `check_that_in` functions
- **ReportPortal**: fix various regressions introduced in 0.17.0

# 0.17.1 (2018-04-11)

- **API**: fix add_test_in_suite and add_tests_in_suite functions missing in `lemoncheesecake.api` module

# 0.17.0 (2018-04-11)

- **API**: replace `add_test_in_suite` and `add_tests_in_suite` functions by `add_test_in_suite`, this function no
  longer modifies the function passed as argument (former functions has been kept and just call the new one,
  `before_test` and `after_test` argument are now ignored)
- **API**: add the ability to log into multiple steps at the same time using `set_step(description, detached=True)`,
  `end_step(description)` and `detached_step(description)` context manager
- **CLI**: when `--passed` or `--skipped` or `--failed` arguments are passed they imply `--from-report` 
  with the default report directory
- **report**: improve check description for `all_of` and `any_of` matchers
- **under the hood**: event management refactoring: instead of passing all event related attributes directly to event
  handlers, everything is now gather in Event classes
- **under the hood**: for logging report data (steps, logs, checks, ...) the `ReportWriter` no longer maintains a
  context to update the `Report` instance, instead, the needed context (report location) is now available in the 
  Event instances (which is set by the `Runtime` class)

# 0.16.6 (2018-03-14)

- **CLI**: add three commands: `lcc top-suites`, `lcc top-tests` and `lcc top-steps` to show suites, tests and steps
  (respectively) ordered by their duration

# 0.16.5 (2018-02-04)

- **API**: add `{check,require,assert}_that_in` functions to make match operations on dict easier
- **API**: add `is_true` and `is_false` matchers
- **lcc report**: use default report dir if the command is called without report path argument

# 0.16.4 (2018-01-31)

- **API**: add a `present` matcher which is a new alias for `anything`
- **API**: fix extra ' ' character in check description generated by `*_that_entry` functions
- **lcc run**: `--help` improvements
- **lcc show**: do not add a trailing ':' when displaying the suite path (to make it easier to cut & paste)

# 0.16.3 (2018-01-28)

- **API**: fix bad tests order in the case they are declared as functions of a module
- **under the hood**: huge refactoring of unit tests

# 0.16.2 (2018-01-12)

- **reporting**: add a new default reporting directory creation strategy: rotate and remove former report directories
  when creating a new report

# 0.16.1 (2018-01-04)

- **CLI**: rename --on-report CLI argument into --from-report
- **CLI**: in lcc diff, improve test status changes handling
- **CLI**: in lcc report, make test path filter argument non-positional

# 0.16.0 (2018-01-03)

- **CLI**: add `lcc diff` command to compare two reports
- **CLI**: add `--on-report` argument to base filter on tests in report instead of tests in project
- **under the hood**: improve lemoncheesecake.testtree API by using generators and properties

# 0.15.6 (2017-12-27)

- **HTML report**: fix line wrap for check description and details

# 0.15.5 (2017-12-25)

- **HTML report**: fix page layout for report in offline mode
- **HTML report**: make more room for check result details

# 0.15.4 (2017-12-22)

- **matchers**: Add multi-line text rendering of `all_of` and `any_of` matchers description and result details
- **HTML report**: Use variable size container (tables) instead of fixed size

# 0.15.3 (2017-12-14)

- **API**: fix disabled test attribute not properly taken into account in add_test_in_suite

# 0.15.2 (2017-12-10)

- **CLI tools**: various fixes and improvement with disabled tests handling
- **Slack**: add a proxy option (`$SLACK_HTTP_PROXY` environment variable)
- **API**: add a new decorator function `@lcc.hidden()` to hide tests/suites from the test tree

# 0.15.1 (2017-12-05)

- **Slack**: better error handling when message sending fails
- **Slack**: check `$SLACK_MESSAGE_TEMPLATE` variables before starting tests
- Fix swapped session teardown outcome

# 0.15.0 (2017-12-04)

- **reporting**: add new reporting backend for ReportPortal (http://reportportal.io/)
- **reporting**: add new reporting backend for Slack
- **API**: `lcc.prepare_attachment` is now a context manager that returns the attachment file path

# 0.14.0 (2017-11-25)

- **API**: add `lcc.conditional` decorator for tests/suites to allow a test/suite to be included in the test tree
  depending on a condition callback result
- **API**: add `lcc.inject_fixture` function that provides fixture injection into a test suite
- **API**: add `lcc.get_fixture` function that allow the retrieval of an executed, session_prerun-scoped, fixture
- **API**: in project class, add a get_report_info, that allow the project to set custom information in the report
- Make version of lemoncheesecake available through API, CLI and generated reports
- lcc stats: indicate disabled tests

# 0.13.0 (2017-11-05)

- **under the hood**: rework reporting using an events sub-system
- **API**: add support for title in report
- **API**: test and suite names can now be set through an optional `name` argument in `test` and `suite` decorators 
- **lcc report**: display full test path

# 0.12.0 (2017-09-05)

- Rewrite the HTML report using React
- Fix regression introduced in 3e4d341 / 0.11.0: lcc run was crashing while running a suite setup
- **under the hood**: introduce two new functions `find_test` and `find_suite` to find a given test / suite from
  its complete path in the test tree
- **under the hood**: rework filter_suites function by generating new suite instances instead of altering existing onces

# 0.11.1 (2017-08-18)

- **API**: make `load_report` return a `BoundReport` (a subclass of Report that provides a `save` method among others)
  instead of `report`, `backend` pair
- **API**: improve `load_report_from_file` exception message when report file can not be read (impacts `lcc report`)
- **HTML report**: avoid UI shaking on mouse over

# 0.11.0 (2017-08-15)

- **CLI**: a new `lcc report` command has been added to display generated reports on the console
- **under the hood**: the filtering feature now works with report's suite instances (see `lemoncheesecake.filter`)
- **under the hood**: simplify exception handling in `lemoncheesecake.cli.command*`

# 0.10.3 (2017-08-11)

- **HTML report**: fix test suites rendering when metadata are available

# 0.10.2 (2017-08-10)

- **HTML report**: fix various issues on extra info mouse over for IE/Edge

# 0.10.1 (2017-08-06)

- **HTML report**: add various extra information on mouse over for suites, tests, steps and logs
- **HTML report**: automatically expand test when report is accessed using an anchor
- **API**: add new suite/test decorator `disabled` to disable a test or a complete suite
- **API**: rename `check` into `log_check` (keep `check` for backward compatibility)
- **API**: in `match_pattern` matcher use `search` instead of `match` of `re` module
- Fix `contains_string` matcher match description message
- Fix `dict` matcher module name into `dict_` to avoid conflicts with builtin `dict`
- **JSON report**: rename `sub_suites` into `suites`

# 0.10.0 (2017-07-16)

- **API**: Change key=value parameters of `project.py` files into a ProjectConfiguration class

# 0.9.1 (2017-07-11)

- Fix JUnit bad test serialization (successful checks reported as failures)

# 0.9.0 (2017-07-09)

- **reporting**: add JUnit reporting backend
- **API**: all methods/functions/classes/modules with the "testsuite" form (whatever the case is) have been renamed into "suite" in order to make the testsuite/suite naming more coherent (both forms were previously used)

# 0.8.12 (2017-07-02)

- **lcc run**: add new CLI options --exit-error-on-failure and --stop-on-failure
- rename `lcc tree` command back into `lcc show`
- Fix `contains_string` matcher

# 0.8.11 (2017-06-15)

- **HTML report**: fix offline mode regression (.html file not loading the correct .js file) introduced in 0.8.10
- **HTML report**: make links associated to tests and testsuites opened in new tab

# 0.8.10 (2017-06-13)

- Rename JSON report data file from 'report.json' into 'report.js' in order to avoid Chrome security policy issue when the report is served by a web server

# 0.8.9 (2017-06-10)

- rename `lcc show` command into `lcc tree`
- remove lemoncheesecake.worker feature (same functionality can be achieved using `setup_suite` method and fixtures)
- README.md: various improvements
- fix various Python warnings
- first release on PyPI

# 0.8.8 (2017-06-01)

- **HTML report**: fix handling of tests being executed at the time of html report rendering (again, regression was introduced in 0.8.7)
- **HTML report**: minor visual improvements
- **CLI**: find project file (`project.py`) also in parent directories
- **matchers**: fix has_entry matcher detail message when no entry is found (double double quotes issue)

# 0.8.7 (2017-05-28)

- Various visual improvements in HTML report

# 0.8.6 (2017-05-23)

- **CLI**: in --help of lcc commands, split arguments by groups
- **matchers**: add a `using_base_key` method in `this_dict` context manager

# 0.8.5 (2017-05-21)

- **API**: Change `*_that_entry` API by passing actual in a 'in_' parameter and add
  a Context Manager named `this_dict` that helps passing the actual value to those functions
- **HTML report**: Fix handling of tests being executed at the time of html report rendering

# 0.8.4 (2017-05-19)

- Add `log_url` function that logs URLs into the report
- Add `is_bool` matcher
- Rename `is_not` matcher into `not_`
- Fix encoding issue when match result description is unicode

# 0.8.3 (2017-05-17)

- Fix crash when using the SAVE_AT_EACH_EVENT report saving mode (JSON & XML)
- Add support for smarter key lookup in imbricated dicts in *has_entry* matcher

# 0.8.2 (2017-05-15)

- Support UserError exception as a 'special' exception when loading testsuites (UserError can now be used for
  example while generating dynamically a testsuite to display an error message to the user)

# 0.8.1 (2017-05-14)

- **matchers**: add the following new matchers: *something*, *existing*, *is_in*, *is_between*
- **matchers**: add a constant *DISPLAY_DETAILS_WHEN_EQUAL* in *lemoncheesecake.matching* that can be used to hide matchers details when the actual value is equal to the expected value
- **matchers**: fix various matcher description wording issues
- **packaging**: set additional metadata information in setuptools

# 0.8.0 (2017-05-08)

- **API**: introduce new lemoncheesecake.matching API
- **API**: replace test outcome by test status

# 0.7.2 (2017-04-17)

- **API**: rank option of @testsuite decorator was no longer properly taken into account (regression introduced in 0.7.0)

# 0.7.1 (2017-04-09)

- **API**: add support for fixtures in setup_suite hook
- minor improvements and fixes

# 0.7.0 (2017-04-02)

- **API**: add support for a new kind of testsuites where the a module can be a testsuite and its functions
  (properly decorated) the tests
- **API**: the public API that must be used to write testsuites is now accessible through lemoncheesecake.api
  instead of lemoncheesecake
- **API**: provide two new generic functions (lemoncheesecake.reporting.{save_report,load_report})
  to read and write a report from/into file

# 0.6.4 (2017-03-14)

- **lcc stats**: show tests percentage
- **lcc stats**: display the number of testsuites which have direct tests

# 0.6.3 (2017-03-12)

- **API**: add a new fixture scope "session_prerun" for fixtures that needs to be
  executed before the test session is started
- **CLI**: various improvements in lcc commands output and error handling
- **CLI**: in filters, add support for '*' characters in property values and links (name & URL)
- **CLI**: in filters, add support for logical AND and OR

# 0.6.2 (2017-02-27)

- Fix project load failure when a fixture relies on 'fixture_name'

# 0.6.1 (2017-02-26)

- **API**: rank option of @testsuite decorator was not properly taken into account
- **API**: new special fixture 'fixture_name'
- **CLI**: for commands show, fixtures and stats, do not display color is the output gets
  redirected, adds a --color option to force it
- **under the hood**: add unit tests for CLI commands

# 0.6.0 (2017-02-19)

- **API**: a testsuite must now be declared using @lcc.testsuite decorator instead of inheriting lcc.TestSuite
- **API**: the @lcc.test decorator now modifies the test method instead of wrapping it into a Test instance
- **API**: Test and TestSuite classes are now only used internally and are disassociated from the representation
  of testsuites and tests for the user
- **CLI**: add a new command 'show' that displays the project test tree
- **CLI**: add a new command 'fixtures' that displays the project fixtures
- **CLI**: add a new command 'stats' that displays various statistics about the project test tree

# 0.5.3 (2017-02-13)

- Add support for negative filters (using a '-' or a '~' or a '^' before the filtered value)

# 0.5.2 (2017-02-09)

- Add a new "add_report_info" function to add key/value info to the report from test context
- After test setup, 'reset' test step to the test description

# 0.5.1 (2017-01-30)

- Fix module loading bug in case of multiple modules share the same name

# 0.5.0 (2017-01-30)

- **API**: test/testsuite ids have been replaced by names (the unicity of (former) ids has been dropped)
- **CLI**: all commands are merge into a single lcc command with sub commands (lcc-run => lcc run, lcc-create-project => lcc bootstrap)
- **CLI**: in lcc run, --test-id and --suite-id has been merged into a single positional test/suite "path" argument
- **CLI**: in lcc run, various filtering bug have been fixed
- **CLI**: improve error handling
- **JSON/XML report**: timestamp are now stored in 'YYYY-MM-DD HH:MM:SS.sss' format instead of float
- **JSON/XML report**: add timestamp in log entries
- **API (checkers)**: add {assert,check}_dict_has_{list,dict} checkers and {assert,check}_choice
- **under the hood**: use tox to do unit testing on Python 2.7/3.3/3.4/3.5/3.6 with/without lxml installed
- **under the hood**: put filtering module under unit testing
- **HTML report**: minor fixes
- various bug fixes and improvements

# 0.4.2 (2017-01-19)

- fix various fixtures dependency handling issues
- add a builtin fixture 'project_dir'
- do not hide python stacktraces in lcc-run

# 0.4.1 (2017-01-17)

- fix several bugs and/or regressions introduced in 0.4.0

# 0.4.0 (2017-01-15)

- **lcc-run**: replace the custom test launcher by a generic test runner (lcc-run) that uses a project.py file to
  retrieve the parameters of the test project; the initial project structure can be created through
  the lcc-create-project command
- **fixtures**: introduce a new fixture system similar to what pytest offers
- use a more standard vocabulary by renaming all methods (and related methods and data) from "before_*" and "after_*" to
  "setup_*" and "teardown_*"
- improve the dependency system between setup and teardown methods (it also apply to fixtures setup/teardown)
- fix save_attachment_content when used with str on Python 3 (a new parameter binary_mode, set to False by default,
  has been introduced)

# 0.3.8 (2016-12-30)

- Various bug fixes, among which: fix binary attachment saving on Windows, be fault tolerant when an exception
  cannot be properly decoded in UTF-8 (on Windows, I already got a stacktrace encoded in mbcs)

# 0.3.7 (2016-12-27)

- **Reporting**: add a configurable save mode for JSON & XML reporting backends allowing the developer
  to indicate at which moment the report should be written on disk
- minor enhancements and bug fixes

# 0.3.6 (2016-12-21)

- **API**: add new checkers for dict data
- **API**: add two new hooks in launcher for custom code that need to run before and/or after the test run
- fix encoding issue in checkers description
- various minor fixes

# 0.3.5 (2016-12-08)

- **API**: add the ability to perform a check within a hook (before/after suite, before/after all tests)
- **API / Report**: add a outcome flag for hooks
- **API**: improve default step description ("-" has been replaced by the current context description)
- **Console reporting**: add the ability display only the current testsuite id instead of the full testsuite path

# 0.3.4 (2016-12-05)

- **HTML report**: fix regressions introduced in 0.3.3
- **Checkers**: minor fixes and improvements
- **Compatibility**: make it work (again) with Python 3
- **Console reporting**: fix minor issue dealing with terminal width and long test id / test steps
- **Unit tests**: add tests for for `lemoncheesecake.checkers`

# 0.3.3 (2016-12-01)

- **HTML report**: escape all the data coming from the JSON report
- **HTML report**: do not display a testsuite header if the testsuite does not contain tests directly
- **Console reporting**: optimize the output depending on the terminal size
- Fix missing check details for some checkers

# 0.3.2 (2016-11-29)

- **Reporting**: Rework the report dir creation so that the rotation mechanism also works on Windows

# 0.3.1 (2016-11-28)

- **API**: multiple workers can now be used
- **API**: worker's hooks execution is now performed within the reporting session context (logs, attachments, etc... can be used in hooks)

# 0.3.0 (2016-11-24)

- **API**: heavy work to improve the reporting layer (lemoncheesecake.reporting) code and API
- **Unit tests**: put lemoncheesecake.runtime module under tests
- **Unit tests**: put XML & JSON serialization/unserialization code under tests
- **Reporting**: make lemoncheesecake installable and usable without lxml

# 0.2.0 (2016-10-31)

- **API**: complete rework of `MetadataPolicy` (previously known as `PropertyValidator`)
- **API**: fix `link`/`tags`/`prop` decorators when applied to a `TestSuite` class
- **API**: the `url` decorator has been renamed into `link`
- **API**: add a new testsuites import function: `import_testsuites_from_files`
- **CLI**: report backends can be enabled or disabled directly from the launcher CLI
- **HTML report**: display testsuite MetadataPolicy
- **HTML report**: minor visual improvements
- **Documentation**: update README.md to cover attachments and `MetadataPolicy`
- **Unit tests**: improve test coverage on testsuites import functions, `Launcher` and `TestSuite` classes
- **Unit tests**: add tests on the new `MetadataPolicy` class

# 0.1.0 (2016-10-06)

- Initial release
