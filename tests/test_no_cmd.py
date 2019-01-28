from helpers.runner import run_main
from helpers.cli import cmdout


def test_no_cmd(cmdout):
    try:
        run_main([])
    except SystemExit:
        pass
    cmdout.assert_substrs_in_line(0, ["usage:"], on_stderr=True)
