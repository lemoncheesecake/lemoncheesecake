import os.path as osp

import lemoncheesecake.api as lcc
from lemoncheesecake.reporting.backends import HtmlBackend

from helpers.runner import run_suite_class


def test_html(tmpdir):
    @lcc.suite()
    class Suite(object):
        @lcc.test()
        def test(self):
            lcc.log_info("something")

    run_suite_class(Suite, backends=(HtmlBackend(),), tmpdir=tmpdir)

    expected = (
        "report.html",
        osp.join(".html", "report.js"),
        osp.join(".html", "report.css"),
        osp.join(".html", "logo.png"),
        osp.join(".html", "bootstrap-icons.css"),
        osp.join(".html", "fonts", "bootstrap-icons.woff"),
        osp.join(".html", "fonts", "bootstrap-icons.woff2")
    )
    for path in expected:
        assert osp.exists(osp.join(tmpdir.strpath, path))
