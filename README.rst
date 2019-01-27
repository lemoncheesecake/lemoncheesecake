lemoncheesecake: a functional test framework for Python
=======================================================

lemoncheesecake makes reporting the first class citizen while providing modern test features such as
fixtures and matchers.

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


Features
--------

- Advanced test hierarchies using suites, tests and nested suites

- Test description and metadata: tags, properties (key=value associations) and links

- Support for test filtering

- Multiple reporting flavors built-in: HTML, JSON, XML, JUnit, ReportPortal, Slack notifications

- Test parallelization

- Rich CLI toolbox

lemoncheesecake is compatible with Python 2.7, 3.4-3.7.


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


Contact
-------

Bugs and improvement ideas are welcomed in tickets. A Google Groups forum is also available for discussions about
lemoncheesecake: https://groups.google.com/forum/#!forum/lemoncheesecake.
