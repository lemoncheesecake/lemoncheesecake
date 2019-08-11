from typing import Optional

import sys
import traceback


class LemoncheesecakeException(Exception):
    message_prefix = None  # type: Optional[str]

    def __str__(self):
        s = Exception.__str__(self)
        if self.message_prefix:
            s = "%s, %s" % (self.message_prefix, s)
        return s


class ProgrammingError(LemoncheesecakeException):
    pass


class ProjectError(LemoncheesecakeException):
    pass


class ModuleImportError(LemoncheesecakeException):
    pass


class FixtureError(LemoncheesecakeException):
    pass


class InvalidSuiteError(LemoncheesecakeException):
    pass


class InvalidMetadataError(ProgrammingError):
    pass


class VisibilityConditionNotMet(LemoncheesecakeException):
    pass


class UnknownReportBackendError(LemoncheesecakeException):
    pass


class AbortTest(LemoncheesecakeException):
    """
    Raising this exception will stop the currently running test.
    """

    message_prefix = "The test has been aborted"

    def __init__(self, reason):
        LemoncheesecakeException.__init__(self, reason)


class AbortSuite(LemoncheesecakeException):
    """
    Raising this exception will stop the currently running suite.
    """
    message_prefix = "The suite has been aborted"

    def __init__(self, reason):
        LemoncheesecakeException.__init__(self, reason)


class AbortAllTests(LemoncheesecakeException):
    """
    Raising this exception will stop the currently running test and all the tests waiting to be run.
    """
    message_prefix = "All tests have been aborted"

    def __init__(self, reason):
        LemoncheesecakeException.__init__(self, reason)


class UserError(LemoncheesecakeException):
    """
    This exception is intended to be raised in pre-run and post-run phases of the project
    to indicate that a required state has not been fulfilled.
    """
    # NB: sphinx requires the constructor to be overriden, otherwise it raises an error
    def __init__(self, reason):
        LemoncheesecakeException.__init__(self, reason)


class InvalidReportFile(LemoncheesecakeException):
    pass


class IncompatibleReportFile(LemoncheesecakeException):
    pass


class CannotFindTreeNode(LemoncheesecakeException):
    pass


class TaskFailure(LemoncheesecakeException):
    pass


class TasksExecutionFailure(LemoncheesecakeException):
    pass


class CircularDependencyError(LemoncheesecakeException):
    pass


def serialize_current_exception(show_stacktrace=True):
    if show_stacktrace:
        return "\n" + "<" * 72 + "\n" + traceback.format_exc() + ">" * 72
    else:
        return " " + str(sys.exc_info()[1])
