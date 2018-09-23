.. _`logging`:

Logging
=======

.. _`logs`:

Logs
----

lemoncheesecake provides logging functions that give the user the ability to log information beyond the checks:

- ``log_debug(msg)``

- ``log_info(msg)``

- ``log_warn(msg)``

- ``log_error(msg)``: this log will mark the test as failed

- ``log_url(url[, description])``

Example:

.. code-block:: python

    lcc.log_debug("Some debug message")
    lcc.log_info("More important, informational message")
    lcc.log_warning("Something looks abnormal")
    lcc.log_error("Something bad happened")
    lcc.log_url("http://example.com", "Example dot com")

.. _`steps`:

Steps
-----

Steps provide a way to organize your logs ad checks within logical steps:

.. code-block:: python

    lcc.set_step("Prepare stuff for test")
    value = 42
    lcc.log_info("Retrieve data for %d" % value)
    data = some_function_that_provide_data(value)
    lcc.log_info("Got data: %s" % data)

    lcc.set_step("Check data")
    check_that_in(
        actual,
        "foo", equal_to(21),
        "bar", equal_to(42)
    )

.. _`attachments`:

Attachments
-----------

Within a test, you also have the possibility to attach files to the report:

.. code-block:: python

    lcc.save_attachment_file(filename, "file.pdf")

The file will be copied into the report dir and is prefixed by a unique value, making it possible to save
multiple times an attachment with the same base file name. The attachment description is optional.

There are other ways to save attachment files depending on your needs.

If the file you want to save is loaded in memory:

.. code-block:: python

    lcc.save_attachment_content(data, "file.pdf", "PDF file")

If you need the effective file path to write into:

.. code-block:: python

    with lcc.prepare_attachment("file.pdf", "PDF file") as filename:
        with open(filename, "w") as fh:
            fh.write(image_data)

Each of these three functions as a corresponding function for image attachment:

- ``save_image_file``

- ``save_attachment_content``

- ``prepare_image_attachment``

In that case, the attached file will be considered as an image
and will be displayed inline in the HTML report.
