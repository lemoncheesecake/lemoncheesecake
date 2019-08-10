.. _`configuring reporting backends`:

Configuring reporting backends
==============================

Some reporting backends require specific configuration, this is done through environment variable.

ReportPortal
------------

The ReportPortal (https://reportportal.io) reporting backend does real time reporting, meaning you can see the
results of your tests during test execution.

- ``LCC_RP_URL``: the URL toward your ReportPortal instance, example: https://reportportal.example.com (mandatory)

- ``LCC_RP_AUTH_TOKEN``: the token with UUID form that is used to authenticate on ReportPortal (mandatory)

- ``LCC_RP_PROJECT``: the ReportPortal project where the test result will be stored (mandatory)

- ``LCC_RP_LAUNCH_NAME``: the ReportPortal launch name (default is "Test Run")

- ``LCC_RP_LAUNCH_DESCRIPTION``: the ReportPortal launch description (optional)

If the ReportPortal instance uses https over plain http, you'll need to explicitly trust the remote server certificate
(unless this certificate has been signed by a trusted CA). This is done by pointing the ``REQUEST_CA_BUNDLE`` environment
variable to a file that contains the remote server certificate chain. It will be the server certificate itself if it's a
self-signed certificate.

Slack
-----

The Slack reporting backend sends a notification at the end of the test run to a given channel or user.

Settings
^^^^^^^^

- ``LCC_SLACK_HTTP_PROXY``: HTTP proxy to use to connect to Slack (optional)

- ``LCC_SLACK_AUTH_TOKEN``: authentication token to connect on Slack (mandatory, the value starts with ``xoxb-``)

- ``LCC_SLACK_CHANNEL``: the channel or the user to send message to (mandatory, syntax: ``#channel`` or ``@user``)

- ``LCC_SLACK_MESSAGE_TEMPLATE``: the message template can contain variables using the form ``{var}``, see below
  for available variables (mandatory)

- ``LCC_SLACK_ONLY_NOTIFY_FAILURE``: if this variable is set, then the notification will only be sent on failures
  (meaning if there is one or more tests with status "failed" or "skipped")

Here are the supported variables for slack message template:

- ``start_time``: the test run start time

- ``end_time``: the test run end time

- ``duration``: the test run duration

- ``total``: the total number of tests (including disabled tests)

- ``enabled``: the total number of tests (excluding disabled tests)

- ``passed``: the number of passed tests

- ``passed_pct``: the number of passed tests in percentage of enabled tests

- ``failed``: the number of failed tests

- ``failed_pct``: the number of failed tests in percentage of enabled tests

- ``skipped``: the number of skipped tests

- ``skipped_pct``: the number of skipped tests in percentage of enabled tests

- ``disabled``: the number of disabled tests

- ``disabled_pct``: the number of disabled tests in percentage of all tests

An example of ``LCC_SLACK_MESSAGE_TEMPLATE``:

``MyProduct test results: {passed}/{enabled} passed ({passed_pct})``

Getting a Slack API access token
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can obtain a Slack API access token for your workspace by following the steps below:

- in your Slack Workspace, click the **Apps** section

- in the Apps page, click **Manage apps...**

- the App Directory page shows up, in this page, make a search using the keyword "bots" in the top text box
  **Search App Directory**

- click **Bots** app > **Add configuration**

- set **Username** and click **Add bot integration**

- you'll get the API access token in **Integration Settings**

NB: please note that there are several ways to get an API token to interact with a Slack Workspace. You could also create
a new Slack App but the method described above seems to be the easier to follow.
