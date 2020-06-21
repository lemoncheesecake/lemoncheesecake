.. _`api`:

API reference
=============

API compatibility / stability
-----------------------------

lemoncheesecake follows the well know `Semantic Versioning <https://semver.org/>`_ for it's public API.
What is considered as "public" is everything which is documented on http://docs.lemoncheesecake.io/. Everything else is
internal and is subject to change at anytime.

.. module:: lemoncheesecake.api

Tests and suites declaration
----------------------------

.. autofunction:: suite
.. autofunction:: test
.. autofunction:: tags
.. autofunction:: prop
.. autofunction:: link
.. autofunction:: disabled
.. autofunction:: visible_if
.. autofunction:: hidden
.. autofunction:: depends_on
.. autofunction:: parametrized
.. autofunction:: inject_fixture
.. autofunction:: add_test_into_suite

.. autoclass:: lemoncheesecake.api.Test
    :members:
    :inherited-members:


Logging
-------

.. autofunction:: set_step
.. autofunction:: detached_step
.. autofunction:: log_info
.. autofunction:: log_warning
.. autofunction:: log_error
.. autofunction:: log_url
.. autofunction:: log_check
.. autofunction:: prepare_attachment
.. autofunction:: prepare_image_attachment
.. autofunction:: save_attachment_content
.. autofunction:: save_attachment_file
.. autofunction:: save_image_content
.. autofunction:: save_image_file


Threading
---------

..  autoclass:: lemoncheesecake.api.Thread


Matching
--------

..  module:: lemoncheesecake.matching


Operations
~~~~~~~~~~

.. autofunction:: check_that
.. autofunction:: require_that
.. autofunction:: assert_that
.. autofunction:: check_that_in
.. autofunction:: require_that_in
.. autofunction:: assert_that_in


Matchers
~~~~~~~~

.. autofunction:: equal_to
.. autofunction:: not_equal_to
.. autofunction:: greater_than
.. autofunction:: greater_than_or_equal_to
.. autofunction:: less_than
.. autofunction:: less_than_or_equal_to
.. autofunction:: is_between
.. autofunction:: is_none
.. autofunction:: is_not_none
.. autofunction:: has_length
.. autofunction:: is_true
.. autofunction:: is_false
.. autofunction:: is_json
.. autofunction:: starts_with
.. autofunction:: ends_with
.. autofunction:: contains_string
.. autofunction:: match_pattern
.. autofunction:: is_text
.. autofunction:: is_integer
.. autofunction:: is_float
.. autofunction:: is_bool
.. autofunction:: is_str
.. autofunction:: is_list
.. autofunction:: is_dict
.. autofunction:: has_item
.. autofunction:: has_items
.. autofunction:: has_only_items
.. autofunction:: is_in
.. autofunction:: has_entry
.. autofunction:: is_
.. autofunction:: not_
.. autofunction:: is_not
.. autofunction:: all_of
.. autofunction:: any_of
.. autofunction:: anything
.. autofunction:: something
.. autofunction:: existing
.. autofunction:: present

Matcher
~~~~~~~

.. module:: lemoncheesecake.matching.matcher

.. autoclass:: Matcher
    :members: build_description, matches

.. autoclass:: MatchResult
    :members: is_successful, description, success, failure, __bool__

.. autoclass:: MatcherDescriptionTransformer
    :members: conjugate, negative, __call__

Project
-------

This is the class that must be used / inherited in your ``project.py`` file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. module:: lemoncheesecake.project

.. autoclass:: Project
    :members: dir, metadata_policy, threaded, show_command_line_in_report, reporting_backends,
        default_reporting_backend_names,
        add_cli_args, create_report_dir, load_suites, load_fixtures, pre_run, post_run, build_report_title,
        build_report_info


Loading suites
~~~~~~~~~~~~~~

.. module:: lemoncheesecake.suite

.. autofunction:: load_suites_from_directory
.. autofunction:: load_suites_from_files
.. autofunction:: load_suite_from_file
.. autofunction:: load_suite_from_module
.. autofunction:: load_suites_from_classes
.. autofunction:: load_suite_from_class


Loading fixtures
~~~~~~~~~~~~~~~~

.. module:: lemoncheesecake.fixture

.. autofunction:: load_fixtures_from_directory
.. autofunction:: load_fixtures_from_files
.. autofunction:: load_fixtures_from_file
.. autofunction:: load_fixtures_from_module
.. autofunction:: load_fixtures_from_func


Metadata Policy
~~~~~~~~~~~~~~~

.. module:: lemoncheesecake.metadatapolicy

.. autoclass:: MetadataPolicy
    :members: add_property_rule, disallow_unknown_properties, add_tag_rule, disallow_unknown_tags

Exceptions
----------

.. module:: lemoncheesecake.exceptions

.. autofunction:: AbortTest
.. autofunction:: AbortSuite
.. autofunction:: AbortAllTests
.. autofunction:: UserError
