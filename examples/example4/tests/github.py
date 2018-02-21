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
