import re

import pytest


@pytest.fixture()
def cmdout(capsys):
    class _CmdOutput:
        def __init__(self):
            self._stdout_lines = None
            self._stderr_lines = None

        def get_lines(self, on_stderr=False):
            if self._stdout_lines is None or self._stderr_lines is None:
                stdout, stderr = capsys.readouterr()
                self._stdout_lines = [line for line in stdout.split("\n")]
                self._stderr_lines = [line for line in stderr.split("\n")]
            return self._stderr_lines if on_stderr else self._stdout_lines

        def assert_substrs_in_line(self, line_nb, substrs, on_stderr=False):
            lines = self.get_lines(on_stderr)
            for substr in substrs:
                assert substr in lines[line_nb]

        def assert_substrs_anywhere(self, substrs, on_stderr=False):
            for line_nb in range(len(self.get_lines(on_stderr))):
                try:
                    self.assert_substrs_in_line(line_nb, substrs, on_stderr)
                except AssertionError:
                    pass
                else:
                    return
            else:
                raise AssertionError()

        def assert_substrs_not_in_line(self, line_nb, substrs, on_stderr=False):
            lines = self.get_lines(on_stderr)
            for substr in substrs:
                assert substr not in lines[line_nb]

        def assert_line_startswith(self, line_nb, substr, on_stderr=False):
            lines = self.get_lines(on_stderr)
            assert lines[line_nb].startswith(substr)

        def assert_line_not_startswith(self, line_nb, substr, on_stderr=False):
            lines = self.get_lines(on_stderr)
            assert not lines[line_nb].startswith(substr)

        def assert_lines_nb(self, lines_nb, on_stderr=False):
            lines = self.get_lines(on_stderr)
            assert len(lines) == lines_nb

        def assert_lines_match(self, pattern, on_stderr=False):
            lines = self.get_lines(on_stderr)
            for line in lines:
                if re.compile(pattern).search(line):
                    return
            raise Exception("No line matches pattern '%s' in \n<<<\n%s\n>>>" % (pattern, "\n".join(lines)))

        def dump(self):
            stdout = self.get_lines()
            stderr = self.get_lines(on_stderr=True)
            print("STDOUT:\n<<<\n%s>>>\n" % "\n".join(stdout))
            print("STDERR:\n<<<\n%s>>>\n" % "\n".join(stderr))

    return _CmdOutput()


def assert_run_output(cmdout, suite_name, successful_tests=[], failed_tests=[], skipped_tests=[]):
    cmdout.assert_lines_match("= %s =" % suite_name)
    for test in successful_tests:
        cmdout.assert_lines_match("OK.+%s" % test)
    for test in failed_tests:
        cmdout.assert_lines_match("KO.+%s" % test)
    for test in skipped_tests:
        cmdout.assert_lines_match("--.+%s" % test)
    cmdout.assert_lines_match("Tests: %d" % (len(successful_tests + failed_tests + skipped_tests)))
    cmdout.assert_lines_match("Successes: %d" % len(successful_tests))
    cmdout.assert_lines_match("Failures: %d" % len(failed_tests))
    if len(skipped_tests) > 0:
        cmdout.assert_lines_match("Skipped: %d" % len(skipped_tests))
