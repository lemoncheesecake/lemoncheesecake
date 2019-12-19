.. _project:

Project customization
=====================

The project file allows the customization of several behaviors of lemoncheesecake.

.. _`add CLI args`:

Add custom CLI arguments to lcc run
-----------------------------------

Custom command line arguments are can be added to ``lcc run``::

    # project.py:

    import os.path

    from lemoncheesecake.project import Project


    class MyProject(Project):
        def add_cli_args(self, cli_parser):
            cli_parser.add_argument("--host", required=True, help="Target host")
            cli_parser.add_argument("--port", type=int, default=443, help="Target port")


    project_dir = os.path.dirname(__file__)
    project = MyProject(project_dir)

And then accessed through the ``cli_args`` fixture::

    # fixtures/fixtures.py:

    def target_url(cli_args):
        return "https://%s:%s" % (cli_args.host, cli_args.port)

``cli_parser`` is an ``ArgumentParser`` instance of the `argparse <https://docs.python.org/2/library/argparse.html>`_ module.

.. _prepostrunhooks:

Running code before and/or after the test session
-------------------------------------------------

Hook methods can be defined to be run before and/or after the test session. Since the code of these methods is not run within
the context of a test session, all functions logging information (such as ``lcc.log_info``, ``check_that``, etc...)
into the report won't be available (they will raise an exception)::

    # project.py:

    import os.path

    from lemoncheesecake.project import Project


    class MyProject(Project):
        def pre_run(self, cli_args, report_dir):
            # do something before the tests are run

        def post_run(self, cli_args, report_dir):
            # do something after the tests are run


    project_dir = os.path.dirname(__file__)
    project = MyProject(project_dir)

An exception raised within the ``pre_run`` method will prevent the tests from being run. The ``lcc.UserError`` exception class
can be used to show the user an error message. Any other exception will be considered as an unexpected error and a
full error stacktrace will be displayed to the user.

Regarding the previous example, please note that the ``pre_run`` and ``post_run`` methods can be defined independently.

.. _reportextrainfo:

Adding extra information in the report
--------------------------------------

Extra key/value pairs can be added to the "Information" section of the report::

    # project.py:

    import os.path

    from lemoncheesecake.project import Project


    class MyProject(Project):
        def build_report_info(self):
            return [
                ("info1", "value1"),
                ("info2", "value2")
            ]


    project_dir = os.path.dirname(__file__)
    project = MyProject(project_dir)

.. _reporttitle:

Setting a custom report tile
----------------------------

A custom report title can also be set::

    # project.py:

    import os.path
    import time

    from lemoncheesecake.project import Project


    class MyProject(Project):
        def build_report_title(self):
            return "This is my test report for %s" % time.asctime()


    project_dir = os.path.dirname(__file__)
    project = MyProject(project_dir)

.. _loadsuitesandfixtures:

Customize suites and fixtures loading
-------------------------------------

The ``Project`` class loads the suites and fixtures respectively from "suites" and "fixtures" directories relative to
the project directory.

Here is an example of project that loads suites and fixtures from alternate directories by overriding the
``load_suites``  and ``load_fixtures`` methods::

    # project.py:

    import os.path

    from lemoncheesecake.project import Project
    from lemoncheesecake.suite import load_suites_from_directory
    from lemoncheesecake.fixture import load_fixtures_from_directory


    class MyProject(Project):
        def load_suites(self):
            return load_suites_from_directory(os.path.join(self.dir, "my_suites"))

        def load_fixtures(self):
            return load_fixtures_from_directory(os.path.join(self.dir, "my_fixtures"))


    project_dir = os.path.dirname(__file__)
    project = MyProject(project_dir)


For more information, see:

- ``load_suite*`` functions from ``lemoncheesecake.suite`` module

- ``load_fixture*`` functions from ``lemoncheesecake.suite`` module

.. _metadatapolicy:

Metadata Policy
---------------

The project settings provides a metadata policy that can be used to add constraints to tests and suites
concerning the usage of metadata.

The following example requires that every tests provide a property "priority" whose value is among "low", "medium" and "high"::

    # project.py:

    import os.path

    from lemoncheesecake.project import Project


    project_dir = os.path.dirname(__file__)
    project = Project(project_dir)
    project.metadata_policy.add_property_rule(
        "priority", ("low", "medium", "high"), required=True
    )

In this other example set, the metadata policy makes two tags available ("todo" and "known_defect") for both tests
and suites while forbidding the usage of any other tag::

    # project.py:
    [...]

    project = Project(project_dir)
    project.metadata_policy.add_tag_rule(
        ("todo", "known_defect"), on_test=True, on_suite=True
    )
    project.disallow_unknown_tags()

See ``lemoncheesecake.metadatapolicy.MetadataPolicy`` for more information.
