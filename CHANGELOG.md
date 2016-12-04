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
