.. _project:

Project customization
=====================

The project file allows the customization of several behaviors of lemoncheesecake.

.. _`add CLI args`:

Add custom CLI arguments
------------------------

Custom command line arguments are can be added to ``lcc run``::

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

And then accessed through the ``cli_args`` fixture::

    # fixtures/fixtures.py:

    def target_url(cli_args):
        return "https://%s:%s" % (cli_args.host, cli_args.port)

``cli_parser`` is an ``ArgumentParser`` instance of the `argparse <https://docs.python.org/2/library/argparse.html>`_ module.

.. _metadatapolicy:

Metadata Policy
---------------

The project settings provides a metadata policy that can be used to add constraints to tests and suites
concerning the usage of metadata.

The following example requires that every tests provide a property "priority" whose value is among "low", "medium" and "high"::

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

In this other example set, the metadata policy makes two tags available ("todo" and "known_defect") for both tests
and suites while forbidding the usage of any other tag::

    # project.py:

    class MyProjectConfiguration(SimpleProjectConfiguration, HasMetadataPolicy):
        def get_metadata_policy(self):
            policy = MetadataPolicy()
            policy.add_tag_rule(
                ("todo", "known_defect"), on_test=True, on_suite=True
            )
            policy.disallow_unknown_tags()
            return policy

See ``lemoncheesecake.validators.MetadataPolicy`` for more information.
