.. image:: https://github.com/lemoncheesecake/lemoncheesecake/blob/master/doc/_static/logo.png?raw=true
    :target: http://lemoncheesecake.io

------------

lemoncheesecake: Test Storytelling
==================================

.. image:: https://github.com/lemoncheesecake/lemoncheesecake/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/lemoncheesecake/lemoncheesecake/actions/workflows/tests.yml

.. image:: https://codecov.io/gh/lemoncheesecake/lemoncheesecake/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/lemoncheesecake/lemoncheesecake

.. image:: https://img.shields.io/pypi/v/lemoncheesecake.svg
    :target: https://pypi.org/project/lemoncheesecake/

.. image:: https://img.shields.io/pypi/pyversions/lemoncheesecake.svg
    :target: https://pypi.org/project/lemoncheesecake/

lemoncheesecake is an end-to-end test framework for Python that brings trust around test results.
It allows test developers to be very explicit about what their tests really do with logging, matchers, file attachments, etc..

Here is a test example:

.. code-block:: python

    import json
    import requests

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *

    URL  = "https://api.github.com/orgs/lemoncheesecake"

    @lcc.suite("Github tests")
    class github:
        @lcc.test("Test Organization end-point")
        def organization(self):
            lcc.set_step("Get lemoncheesecake organization information")
            lcc.log_info("GET %s" % URL)
            resp = requests.get(URL)
            require_that("HTTP code", resp.status_code, is_(200))
            data = resp.json()
            lcc.log_info("Response\n%s" % json.dumps(data, indent=4))

            lcc.set_step("Check API response")
            check_that_in(
                data,
                "type", is_("Organization"),
                "id", is_integer(),
                "description", is_not_none(),
                "login", is_(present()),
                "created_at", match_pattern("^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"),
                "has_organization_projects", is_true(),
                "followers", is_(greater_than_or_equal_to(0)),
                "following", is_(greater_than_or_equal_to(0)),
                "repos_url", ends_with("/repos"),
                "issues_url", ends_with("/issues"),
                "events_url", ends_with("/events"),
                "hooks_url", ends_with("/hooks"),
                "members_url", ends_with("/members{/member}"),
                "public_members_url", ends_with("/public_members{/member}")
            )

And here are the corresponding test results:

.. image:: https://github.com/lemoncheesecake/lemoncheesecake/blob/master/doc/_static/report-sample.png?raw=true
    :alt: test results

NB: in real test code, you'd better use
`lemoncheesecake-requests <https://github.com/lemoncheesecake/lemoncheesecake-requests>`_ when doing HTTP / REST API
testing.

Features
--------

- Advanced test hierarchies using suites, tests and nested suites

- Test description and metadata: tags, properties (key=value associations) and links

- Support for test filtering

- Multiple reporting flavors built-in: HTML, JSON, XML, JUnit, ReportPortal, Slack notifications

- BDD support using `behave <https://behave.readthedocs.io/en/latest/>`_

- Test parallelization

- Rich CLI toolbox

lemoncheesecake is compatible with Python 2.7, 3.6-3.10.


Installation
------------

lemoncheesecake can be installed through pip:

.. code-block:: shell

    $ pip install lemoncheesecake

For more details about installing lemoncheesecake with the non-default reporting backends, see
`here <http://docs.lemoncheesecake.io/en/latest/installation.html>`_.


Documentation
-------------

The documentation is available on http://docs.lemoncheesecake.io.

The lemoncheesecake ecosystem
-----------------------------

For HTTP / REST API / Web Services testing, it is recommended to use
`lemoncheesecake-requests <https://github.com/lemoncheesecake/lemoncheesecake-requests>`_ which provides logging
and response checking features for `requests <https://docs.python-requests.org/en/master/>`_.

Contact
-------

Bugs and improvement ideas are welcomed in tickets. A Google Groups forum is also available for discussions about
lemoncheesecake: https://groups.google.com/forum/#!forum/lemoncheesecake.
