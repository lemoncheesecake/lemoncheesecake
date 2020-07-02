.. _report:

Report
======

.. versionadded:: 1.6.0

Since version 1.6.0, lemoncheesecake provides an API to read the reports generated during test runs.
The entry-point of this API is the :func:`load_report() <lemoncheesecake.reporting.load_report>` function which returns
a :class:`Report <lemoncheesecake.reporting.Report>` instance. From this object, every report details
(suites, tests, logs, etc...) is accessible.

The complete API reference is available :class:`here <lemoncheesecake.reporting>`.

In this page, the API is demonstrated through two use cases.

Example 1: generating a CSV file from a report
----------------------------------------------

This example script takes a report path (file or directory) as first argument and generate a CSV representation from this report::

    #!/usr/bin/env python3

    import sys
    import csv

    from lemoncheesecake.reporting import load_report

    def test_to_dict(test):
        return {
            "test": test.path,
            "description": test.description,
            "status": test.status,
            "tags": ",".join(test.tags)
        }

    report = load_report(sys.argv[1])
    csv_writer = csv.DictWriter(sys.stdout, ("test", "description", "status", "tags"))
    csv_writer.writeheader()
    csv_writer.writerows(map(test_to_dict, report.all_tests()))

.. code-block:: console

    $ ./report-to-csv.py report/
    test,description,status,tags
    suite.test_1,My First Test,passed,some_tag
    suite.test_2,My Second Test,failed,


Example 2: generating a summary of the report results
-----------------------------------------------------

This example script takes a report path (file or directory) as first argument and generate a short summary from it::

    #!/usr/bin/env python3

    import sys
    import csv

    from lemoncheesecake.reporting import load_report

    report = load_report(sys.argv[1])
    print(report.build_message("Test results: {passed}/{enabled} passed ({passed_pct}) in {duration}"))

.. code-block:: console

    $ ./report-to-csv.py report/
    Test results: 1/2 passed (50%) in 3s
