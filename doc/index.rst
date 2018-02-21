.. lemoncheesecake documentation master file, created by
   sphinx-quickstart on Wed Feb  7 00:13:33 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _index:

:orphan:

lemoncheesecake: a functional test framework for Python
=======================================================

lemoncheesecake makes reporting feature the first class citizen while providing modern test features such as
fixtures and matchers.

Here is an example of test:

.. code-block:: python

    import json
    import requests

    import lemoncheesecake.api as lcc
    from lemoncheesecake.matching import *

    SUITE = {
        "description": "Github tests"
    }

    URL = "https://api.github.com/orgs/lemoncheesecake"


    @lcc.test("Test Organization end-point")
    def organization():
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

And the corresponding HTML report:

.. image:: _static/report-sample.png

See :ref:`Getting Started <getting started>` to create your first test project.

In short, lemoncheesecake provides:

- a way to organize complex test hierachies using suites, tests, and nested suites

- all tests and suites have a name, a description and also metadata: tags, properties (key=value associations) and links;
  all these information can be used for filtering

- multiple reporting flavors built-in: HTML, JSON, XML, JUnit, ReportPortal, Slack notifications

lemoncheesecake is compatible with Python 2.7, 3.3-3.6.

Installation and configuration
------------------------------

- :ref:`Installation <installation>`

- :ref:`Configuring reporting backends <configuring reporting backends>`


Writing tests
-------------

- :ref:`Getting started <getting started>`

- :ref:`Tests and suites organization <tests and suites>`

- :ref:`Using matchers <matchers>`

- :ref:`Logging data <logging>`

- :ref:`Setup and teardown methods <setup_teardown>`, :ref:`fixtures <fixtures>`

- :ref:`The lcc command line tool and filtering arguments <cli>`

- :ref:`Project customization <project>`

Contact
-------

Bugs and improvement ideas are welcomed in tickets.
A Google Groups forum is also available for discussions about lemoncheesecake:
https://groups.google.com/forum/#!forum/lemoncheesecake .

License
-------

lemoncheeseake is licensed under the
`Apache License <https://github.com/lemoncheesecake/lemoncheesecake/blob/master/LICENSE.txt>`_
