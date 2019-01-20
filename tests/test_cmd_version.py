from lemoncheesecake import __version__

from helpers.runner import run_main
from helpers.cli import cmdout


def test_version_as_arg(cmdout):
    try:
        run_main(["-v"])
    except SystemExit:
        pass
    cmdout.assert_substrs_in_line(0, [__version__])


def test_version_as_cmd(cmdout):
    assert run_main(["version"]) == 0
    cmdout.assert_substrs_in_line(0, [__version__])
