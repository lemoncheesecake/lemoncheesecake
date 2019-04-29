.. _`v1 migration guide`:

V1 migration guide
==================

This page lists all the non-compatible changes between 0.22.x and 1.x versions of lemoncheesecake and how
to migrate.

API
---

Matchers
^^^^^^^^

The following functions have been removed:

- ``this_dict``

- ``check_that_entry``

- ``require_that_entry``

- ``assert_that_entry``

The corresponding ``check_that_in``, ``require_that_in`` and ``assert_that_in`` functions must be used instead.


Fixtures
^^^^^^^^

The fixture scope ``session_prerun`` has been renamed into ``pre_run``.


Attachment logs
^^^^^^^^^^^^^^^

The ``binary_mode`` argument of the ``save_attachment_content`` function has been removed. The file opening mode
is now automatically determined upon the type of data passed as argument.
