from helpers.cli import cmdout
from helpers.report import report_in_progress_path
from helpers.report import make_test_result, make_suite_result, make_report

from lemoncheesecake.cli import main
from lemoncheesecake.reporting.backends.json_ import save_report_into_file
from lemoncheesecake.testtree import flatten_tests
from lemoncheesecake.cli.commands.diff import compute_diff


def check_diff(diff, added=[], removed=[], status_changed=[]):
    assert [t.path for t in diff.added] == added
    assert [t.path for t in diff.removed] == removed
    for test_path, old_status, new_status in status_changed:
        assert test_path in [t.path for t in diff.status_changed[old_status][new_status]]


def test_added_test():
    suite_1 = make_suite_result("mysuite", tests=[make_test_result("mytest1")])
    suite_2 = make_suite_result("mysuite", tests=[make_test_result("mytest1"), make_test_result("mytest2")])
    tests_1 = list(flatten_tests([suite_1]))
    tests_2 = list(flatten_tests([suite_2]))

    diff = compute_diff(tests_1, tests_2)

    check_diff(diff, added=["mysuite.mytest2"])


def test_removed_test():
    suite_1 = make_suite_result("mysuite", tests=[make_test_result("mytest1"), make_test_result("mytest2")])
    suite_2 = make_suite_result("mysuite", tests=[make_test_result("mytest1")])
    tests_1 = list(flatten_tests([suite_1]))
    tests_2 = list(flatten_tests([suite_2]))

    diff = compute_diff(tests_1, tests_2)

    check_diff(diff, removed=["mysuite.mytest2"])


def test_passed_to_failed():
    suite_1 = make_suite_result("mysuite", tests=[make_test_result("mytest1", status="passed")])
    suite_2 = make_suite_result("mysuite", tests=[make_test_result("mytest1", status="failed")])
    tests_1 = list(flatten_tests([suite_1]))
    tests_2 = list(flatten_tests([suite_2]))

    diff = compute_diff(tests_1, tests_2)

    check_diff(diff, status_changed=[["mysuite.mytest1", "passed", "failed"]])


def test_failed_to_passed():
    suite_1 = make_suite_result("mysuite", tests=[make_test_result("mytest1", status="failed")])
    suite_2 = make_suite_result("mysuite", tests=[make_test_result("mytest1", status="passed")])
    tests_1 = list(flatten_tests([suite_1]))
    tests_2 = list(flatten_tests([suite_2]))

    diff = compute_diff(tests_1, tests_2)

    check_diff(diff, status_changed=[["mysuite.mytest1", "failed", "passed"]])


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
    old_report = make_report([
        make_suite_result("mysuite", tests=[
            make_test_result("mytest1"),
            make_test_result("mytest2", status="failed"),
            make_test_result("mytest3")
        ])
    ])
    old_report_path = tmpdir.join("old_report.json").strpath
    save_report_into_file(old_report, old_report_path)

    new_report = make_report([
        make_suite_result("mysuite", tests=[
            make_test_result("mytest1", status="failed"),
            make_test_result("mytest2"),
            make_test_result("mytest4")
        ])
    ])
    new_report_path = tmpdir.join("new_report.json").strpath
    save_report_into_file(new_report, new_report_path)

    assert main(["diff", old_report_path, new_report_path]) == 0

    lines = cmdout.get_lines()
    splitted = _split_lines(lines, "")
    added = next(splitted)
    removed = next(splitted)
    status_changed = next(splitted)

    assert "mysuite.mytest4" in added[1]
    assert "mysuite.mytest3" in removed[1]
    assert "mysuite.mytest2" in status_changed[1]
    assert "mysuite.mytest1" in status_changed[2]


def test_diff_cmd_test_run_in_progress(report_in_progress_path, cmdout):
    assert main(["diff", report_in_progress_path, report_in_progress_path]) == 0

    cmdout.assert_substrs_anywhere("no difference")
