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
