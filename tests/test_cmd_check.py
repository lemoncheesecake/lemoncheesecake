import os.path as osp
import re

from helpers.runner import generate_project, run_main
from helpers.cli import cmdout
from helpers.utils import change_dir, tmp_cwd


def test_everything_is_ok(tmp_cwd, cmdout):
    generate_project(
        ".", "s",
        """import lemoncheesecake.api as lcc

@lcc.test()
def test():
    pass
"""
    )

    run_main(["check"])

    cmdout.assert_lines_match("Everything is ok")


def test_project_dir_arg(tmp_cwd, cmdout, tmp_path_factory):
    generate_project(
        ".", "s",
        """import lemoncheesecake.api as lcc

@lcc.test()
def test():
    pass
"""
    )

    new_dir = tmp_path_factory.mktemp("new_dir")
    with change_dir(str(new_dir)):
        run_main(["check", "-p", tmp_cwd])

    cmdout.assert_lines_match("Everything is ok")


def test_invalid_project(tmp_cwd):
    with open(osp.join(tmp_cwd, "project.py"), "w") as fh:
        fh.write("THIS IS NOT PYTHON CODE")

    assert re.compile(r"Error while importing file.+project\.py").match(run_main(["check"]))


def test_invalid_suite(tmp_cwd):
    generate_project(
        ".", "suite", "THIS IS NOT PYTHON CODE"
    )

    assert re.compile(r"Error while importing file.+suite\.py").match(run_main(["check"]))


def test_fixture_error(tmp_cwd):
    generate_project(
        ".", "s",
        """import lemoncheesecake.api as lcc

@lcc.test()
def test(unknown_fixture):
    pass
"""
    )

    assert "Unknown fixture 'unknown_fixture'" in run_main(["check"])


def test_metadata_policy_compliance_error(tmp_cwd):
    generate_project(
        ".", "s",
        module_content="""import lemoncheesecake.api as lcc

@lcc.test()
@lcc.tags("tag")
def test():
    pass
""",
        project_content="""from lemoncheesecake.project import Project

project = Project()
project.metadata_policy.disallow_unknown_tags()
"""
    )

    assert "tag 'tag' is not allowed" in run_main(["check"])
