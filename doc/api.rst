.. _`api`:

API reference
=============

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


Matchers
~~~~~~~~

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
.. autofunction:: starts_with
.. autofunction:: ends_with
.. autofunction:: contains_string
.. autofunction:: match_pattern
.. autofunction:: is_text
.. autofunction:: is_json
.. autofunction:: has_item
.. autofunction:: has_values
.. autofunction:: has_only_values
.. autofunction:: is_in
.. autofunction:: has_entry
.. autofunction:: is_integer
.. autofunction:: is_float
.. autofunction:: is_bool
.. autofunction:: is_str
.. autofunction:: is_dict
.. autofunction:: is_list
.. autofunction:: all_of
.. autofunction:: any_of
.. autofunction:: anything
.. autofunction:: something
.. autofunction:: existing
.. autofunction:: present
.. autofunction:: is_
.. autofunction:: not_


Project
-------

This is the class that must be used / inherited in your ``project.py`` file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. module:: lemoncheesecake.project

.. autoclass:: Project
    :members: dir, metadata_policy, threaded, reporting_backends, default_reporting_backend_names,
        add_cli_args, create_report_dir, load_suites, load_fixtures, pre_run, post_run, build_report_title,
        build_report_info

All the functions that can be used to load suites within a project file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. module:: lemoncheesecake.suite

.. autofunction:: load_suites_from_directory
.. autofunction:: load_suites_from_files
.. autofunction:: load_suite_from_file
.. autofunction:: load_suite_from_module
.. autofunction:: load_suites_from_classes
.. autofunction:: load_suite_from_class

All the functions that can be used to load fixtures within a project file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. module:: lemoncheesecake.fixture

.. autofunction:: load_fixtures_from_directory
.. autofunction:: load_fixtures_from_files
.. autofunction:: load_fixtures_from_file
.. autofunction:: load_fixtures_from_func


Exceptions
----------

.. module:: lemoncheesecake.exceptions

.. autofunction:: AbortTest
.. autofunction:: AbortSuite
.. autofunction:: AbortAllTests
.. autofunction:: UserError
