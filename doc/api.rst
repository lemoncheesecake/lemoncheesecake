.. _`api`:

API reference
=============

API compatibility / stability
-----------------------------

lemoncheesecake follows the well know `Semantic Versioning <https://semver.org/>`_ for it's public API.
What is considered as "public" is everything which is documented on http://docs.lemoncheesecake.io/. Everything else is
internal and is subject to change at anytime.

.. module:: lemoncheesecake.api

Tests and suites
----------------

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


Fixtures
--------

.. autofunction:: fixture


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

.. autoclass:: lemoncheesecake.api.Thread

.. autoclass:: lemoncheesecake.api.ThreadedFactory
    :members:

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
.. autofunction:: has_all_items
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


Report
------

.. versionadded:: 1.6.0

The structure of a Report object is the following:

.. parsed-literal::

    Report (:class:`~lemoncheesecake.reporting.Report`)
        (0-1) test_session_setup (:class:`~lemoncheesecake.reporting.Result`)
            (1-N) steps (:class:`~lemoncheesecake.reporting.Step`)
                (1-N) step logs (:class:`~lemoncheesecake.reporting.StepLog`)
        (1-N) suites (:class:`~lemoncheesecake.reporting.SuiteResult`)
            (0-1) suite_setup (:class:`~lemoncheesecake.reporting.Result`)
                (1-N) steps (:class:`~lemoncheesecake.reporting.Step`)
                    (1-N) step logs (:class:`~lemoncheesecake.reporting.StepLog`)
            (N) tests (:class:`~lemoncheesecake.reporting.TestResult`)
                (N) steps (:class:`~lemoncheesecake.reporting.Step`)
                    (1-N) step logs (:class:`~lemoncheesecake.reporting.StepLog`)
            (N) sub-suites (:class:`~lemoncheesecake.reporting.SuiteResult`)
                [suites can embed other sub-suite hierarchy]
            (0-1) suite_teardown (:class:`~lemoncheesecake.reporting.Result`)
                (1-N) steps (:class:`~lemoncheesecake.reporting.Step`)
                    (1-N) step logs (:class:`~lemoncheesecake.reporting.StepLog`)
        (0-1) test_session_teardown (:class:`~lemoncheesecake.reporting.Result`)
            (1-N) steps (:class:`~lemoncheesecake.reporting.Step`)
                (1-N) step logs (:class:`~lemoncheesecake.reporting.StepLog`)

    Step logs (whose base class is :class:`~lemoncheesecake.reporting.StepLog`) are one of:
        - :class:`~lemoncheesecake.reporting.Log`
        - :class:`~lemoncheesecake.reporting.Check`
        - :class:`~lemoncheesecake.reporting.Attachment`
        - :class:`~lemoncheesecake.reporting.Url`

.. module:: lemoncheesecake.reporting

.. autofunction:: load_report

.. autoclass:: Report
    :members: start_time, end_time, duration, saving_time, title, nb_threads, test_session_setup, test_session_teardown,
        nb_tests, parallelized, add_info, add_suite, get_suites, is_successful,
        all_suites, all_tests, all_results, all_steps, build_message, save

.. autoclass:: SuiteResult
    :members: start_time, end_time, duration, path, suite_setup, suite_teardown, get_tests, get_suites, add_test, add_suite

.. autoclass:: Result
    :members: STATUSES, parent_suite, type, start_time, end_time, duration, status, status_details, add_step, get_steps, is_successful

.. autoclass:: TestResult
    :members: path

.. autoclass:: Step
    :members: description, start_time, end_time, duration, add_log, get_logs, is_successful

.. autoclass:: StepLog
    :members: time, parent_step

.. autoclass:: Log
    :members: level, message

.. autoclass:: Check
    :members: description, is_successful, details

.. autoclass:: Attachment
    :members: description, filename, as_image

.. autoclass:: Url
    :members: description, url


Exceptions
----------

.. module:: lemoncheesecake.exceptions

.. autofunction:: AbortTest
.. autofunction:: AbortSuite
.. autofunction:: AbortAllTests
.. autofunction:: UserError
