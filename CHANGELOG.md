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

# 0.1.0 (2016-10-01)

- Initial release
