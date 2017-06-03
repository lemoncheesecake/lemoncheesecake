import json
import requests

import lemoncheesecake.api as lcc
from lemoncheesecake.matching import *

URL  = "https://api.github.com/orgs/lemoncheesecake"

@lcc.testsuite("Github tests")
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
        with this_dict(data):
            check_that_entry("type", is_("Organization"))
            check_that_entry("id", is_integer())
            check_that_entry("description", is_not_none())
            check_that_entry("login", is_(existing()))
            check_that_entry("created_at", match_pattern("^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"))
            check_that_entry("has_organization_projects", is_bool(True))
            check_that_entry("followers", greater_than_or_equal_to(0))
            check_that_entry("following", greater_than_or_equal_to(0))
            check_that_entry("repos_url", ends_with("/repos"))
            check_that_entry("issues_url", ends_with("/issues"))
            check_that_entry("events_url", ends_with("/events"))
            check_that_entry("hooks_url", ends_with("/hooks"))
            check_that_entry("members_url", ends_with("/members{/member}"))
            check_that_entry("public_members_url", ends_with("/public_members{/member}"))
