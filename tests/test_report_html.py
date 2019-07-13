import os.path as osp
import glob

import lemoncheesecake.api as lcc
from lemoncheesecake.reporting.backends import HtmlBackend

from helpers.runner import run_suite_class


@lcc.suite("suite")
class Suite(object):
    @lcc.test("test")
    def test(self):
        lcc.log_info("something")


def test_html_fat(tmpdir):
    run_suite_class(Suite, backends=(HtmlBackend(),), tmpdir=tmpdir)
    assert osp.exists(osp.join(tmpdir.strpath, "report.html"))
    assert glob.glob(osp.join(tmpdir.strpath, ".html", "bootstrap*"))


def test_html_non_fat(tmpdir):
    backend = HtmlBackend()
    backend.fat_html = False
    run_suite_class(Suite, backends=(backend,), tmpdir=tmpdir)
    assert osp.exists(osp.join(tmpdir.strpath, "report.html"))
    assert not glob.glob(osp.join(tmpdir.strpath, ".html", "bootstrap*"))
