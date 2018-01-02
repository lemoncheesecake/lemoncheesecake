from helpers import cmdout
from testtreemockup import report_mockup, suite_mockup, tst_mockup, make_report_from_mockup, make_suite_data_from_mockup

from lemoncheesecake.cli import main
from lemoncheesecake.reporting.backends.json_ import save_report_into_file
from lemoncheesecake.cli.commands.diff import compute_diff


def check_diff(diff, added=[], removed=[], passed=[], non_passed=[]):
    assert [t.path for t in diff.added] == added
    assert [t.path for t in diff.removed] == removed
    assert [t.path for t in diff.passed] == passed
    assert [t.path for t in diff.non_passed] == non_passed


def test_added_test():
    old_suite = suite_mockup("mysuite").add_test(tst_mockup("mytest1"))
    new_suite = suite_mockup("mysuite").add_test(tst_mockup("mytest1")).add_test(tst_mockup("mytest2"))

    diff = compute_diff([make_suite_data_from_mockup(old_suite)], [make_suite_data_from_mockup(new_suite)])

    check_diff(diff, added=["mysuite.mytest2"])


def test_removed_test():
    old_suite = suite_mockup("mysuite").add_test(tst_mockup("mytest1")).add_test(tst_mockup("mytest2"))
    new_suite = suite_mockup("mysuite").add_test(tst_mockup("mytest1"))

    diff = compute_diff([make_suite_data_from_mockup(old_suite)], [make_suite_data_from_mockup(new_suite)])

    check_diff(diff, removed=["mysuite.mytest2"])


def test_passed_to_failed():
    old_suite = suite_mockup("mysuite").add_test(tst_mockup("mytest1", status="passed"))
    new_suite = suite_mockup("mysuite").add_test(tst_mockup("mytest1", status="failed"))

    diff = compute_diff([make_suite_data_from_mockup(old_suite)], [make_suite_data_from_mockup(new_suite)])

    check_diff(diff, non_passed=["mysuite.mytest1"])


def test_failed_to_passed():
    old_suite = suite_mockup("mysuite").add_test(tst_mockup("mytest1", status="failed"))
    new_suite = suite_mockup("mysuite").add_test(tst_mockup("mytest1", status="passed"))

    diff = compute_diff([make_suite_data_from_mockup(old_suite)], [make_suite_data_from_mockup(new_suite)])

    check_diff(diff, passed=["mysuite.mytest1"])


def _split_lines(lines, separator):
    group = []
    for line in lines:
        if line == separator:
            if len(group) > 0:
                yield group
                group = []
        else:
            group.append(line)


def test_diff_cmd(tmpdir, cmdout):
    old_report = report_mockup()
    old_report.add_suite(
        suite_mockup("mysuite").
            add_test(tst_mockup("mytest1", status="passed")).
            add_test(tst_mockup("mytest2", status="failed")).
            add_test(tst_mockup("mytest3"))
    )

    new_report = report_mockup()
    new_report.add_suite(
        suite_mockup("mysuite").
            add_test(tst_mockup("mytest1", status="failed")).
            add_test(tst_mockup("mytest2", status="passed")).
            add_test(tst_mockup("mytest4"))
    )

    old_report_path = tmpdir.join("old_report.json").strpath
    save_report_into_file(make_report_from_mockup(old_report), old_report_path)

    new_report_path = tmpdir.join("new_report.json").strpath
    save_report_into_file(make_report_from_mockup(new_report), new_report_path)

    assert main(["diff", old_report_path, new_report_path]) == 0

    lines = cmdout.get_lines()
    splitted = _split_lines(lines, "")
    added = next(splitted)
    removed = next(splitted)
    passed = next(splitted)
    non_passed = next(splitted)

    assert "mysuite.mytest4" in added[1]
    assert "mysuite.mytest3" in removed[1]
    assert "mysuite.mytest2" in passed[1]
    assert "mysuite.mytest1" in non_passed[1]
