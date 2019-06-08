'''
Created on Sep 8, 2016

@author: nicolas
'''

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


class LemoncheesecakeInternalError(LemoncheesecakeException):
    pass
InternalError = LemoncheesecakeInternalError


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
    message_prefix = "The test has been aborted"

    def __init__(self, reason):
        LemoncheesecakeException.__init__(self, reason)


class AbortSuite(LemoncheesecakeException):
    message_prefix = "The suite has been aborted"

    def __init__(self, reason):
        LemoncheesecakeException.__init__(self, reason)


class AbortAllTests(LemoncheesecakeException):
    message_prefix = "All tests have been aborted"

    def __init__(self, reason):
        LemoncheesecakeException.__init__(self, reason)


class UserError(LemoncheesecakeException):
    pass


class InvalidReportFile(LemoncheesecakeException):
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
