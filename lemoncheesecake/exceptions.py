import sys
import traceback


class LemoncheesecakeException(Exception):
    pass


class ProjectLoadingError(LemoncheesecakeException):
    pass


class ProjectNotFound(ProjectLoadingError):
    pass


class ModuleImportError(LemoncheesecakeException):
    pass


class FixtureConstraintViolation(LemoncheesecakeException):
    pass


class SuiteLoadingError(LemoncheesecakeException):
    pass


class FixtureLoadingError(LemoncheesecakeException):
    pass


class MetadataPolicyViolation(LemoncheesecakeException):
    pass


class AbortTest(LemoncheesecakeException):
    """
    Raising this exception will stop the currently running test.
    """
    # NB: sphinx requires the constructor to be overridden, otherwise it raises an error
    def __init__(self, *args):
        LemoncheesecakeException.__init__(self, *args)


class AbortSuite(LemoncheesecakeException):
    """
    Raising this exception will stop the currently running suite.
    """
    # NB: sphinx requires the constructor to be overridden, otherwise it raises an error
    def __init__(self, *args):
        LemoncheesecakeException.__init__(self, *args)


class AbortAllTests(LemoncheesecakeException):
    """
    Raising this exception will stop the currently running test and all the tests waiting to be run.
    """
    # NB: sphinx requires the constructor to be overridden, otherwise it raises an error
    def __init__(self, *args):
        LemoncheesecakeException.__init__(self, *args)


class UserError(LemoncheesecakeException):
    """
    This exception is intended to be raised in pre-run and post-run phases of the project
    to indicate that a required state has not been fulfilled.
    """
    # NB: sphinx requires the constructor to be overridden, otherwise it raises an error
    def __init__(self, *args):
        LemoncheesecakeException.__init__(self, *args)


class ReportLoadingError(LemoncheesecakeException):
    pass


class TaskFailure(LemoncheesecakeException):
    pass


def serialize_current_exception(show_stacktrace=True):
    if show_stacktrace:
        return "\n" + "<" * 72 + "\n" + traceback.format_exc() + ">" * 72
    else:
        return " " + str(sys.exc_info()[1])
