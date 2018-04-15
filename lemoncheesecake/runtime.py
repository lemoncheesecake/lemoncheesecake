'''
Created on Jan 24, 2016

@author: nicolas
'''

import os.path
from contextlib import contextmanager
import shutil
import threading
import traceback

from lemoncheesecake.utils import IS_PYTHON3
from lemoncheesecake.exceptions import LemonCheesecakeInternalError
from lemoncheesecake.consts import ATTACHEMENT_DIR, \
    LOG_LEVEL_DEBUG, LOG_LEVEL_ERROR, LOG_LEVEL_INFO, LOG_LEVEL_WARN
from lemoncheesecake.reporting import *
from lemoncheesecake import events
from lemoncheesecake.exceptions import ProgrammingError

__all__ = "log_debug", "log_info", "log_warn", "log_warning", "log_error", "log_url", "log_check", \
    "set_step", "end_step", "detached_step", \
    "prepare_attachment", "save_attachment_file", "save_attachment_content", \
    "add_report_info", "get_fixture"


_runtime = None  # singleton


def initialize_runtime(report_dir, report, fixture_registry):
    global _runtime
    _runtime = _Runtime(report_dir, report, fixture_registry)
    events.add_listener(_runtime)


def get_runtime():
    if not _runtime:
        raise LemonCheesecakeInternalError("Runtime is not initialized")
    return _runtime


class _Runtime:
    def __init__(self, report_dir, report, fixture_registry):
        self.report_dir = report_dir
        self.report = report
        self.fixture_registry = fixture_registry
        self.attachments_dir = os.path.join(self.report_dir, ATTACHEMENT_DIR)
        self.attachment_count = 0
        self.step_lock = False
        self.location = None
        self._local = threading.local()

    def set_step(self, description, force_lock=False, detached=False):
        if self.step_lock and not force_lock:
            return

        self._local.step = description
        events.fire(events.StepEvent(self.location, description, detached=detached))

    def end_step(self, step):
        events.fire(events.StepEndEvent(self.location, step))

    def _get_step(self, step):
        return step if step is not None else self._local.step

    def log(self, level, content, step=None):
        events.fire(events.LogEvent(self.location, self._get_step(step), level, content))

    def log_check(self, description, outcome, details, step=None):
        events.fire(events.CheckEvent(self.location, self._get_step(step), description, outcome, details))

    def log_url(self, url, description, step=None):
        events.fire(events.LogUrlEvent(self.location, self._get_step(step), url, description))

    @contextmanager
    def prepare_attachment(self, filename, description, step=None):
        attachment_filename = "%04d_%s" % (self.attachment_count + 1, filename)
        self.attachment_count += 1
        if not os.path.exists(self.attachments_dir):
            os.mkdir(self.attachments_dir)

        yield os.path.join(self.attachments_dir, attachment_filename)

        events.fire(events.LogAttachmentEvent(
            self.location, self._get_step(step), "%s/%s" % (ATTACHEMENT_DIR, attachment_filename), filename, description
        ))

    def save_attachment_file(self, filename, description, step=None):
        with self.prepare_attachment(os.path.basename(filename), description, step=step) as report_attachment_path:
            shutil.copy(filename, report_attachment_path)

    def save_attachment_content(self, content, filename, description, binary_mode, step=None):
        with self.prepare_attachment(filename, description, step=step) as report_attachment_path:
            with open(report_attachment_path, "wb") as fh:
                fh.write(content if binary_mode else content.encode("utf-8"))

    def get_fixture(self, name):
        try:
            scope = self.fixture_registry.get_fixture_scope(name)
        except KeyError:
            raise ProgrammingError("Fixture '%s' does not exist" % name)

        if scope != "session_prerun":
            raise ProgrammingError("Fixture '%s' has scope '%s' while only fixtures with scope 'session_prerun' can be retrieved" % (
                name, scope
            ))

        try:
            return self.fixture_registry.get_fixture_result(name)
        except AssertionError as excp:
            raise ProgrammingError(str(excp))


def set_step(description, force_lock=False, detached=False):
    """
    Set a new step.
    """
    get_runtime().set_step(description, force_lock=force_lock, detached=detached)


def end_step(step):
    """
    End a detached step.
    """
    get_runtime().end_step(step)


@contextmanager
def detached_step(description):
    set_step(description, detached=True)
    try:
        yield
    except Exception:
        # FIXME: use exception instead of last implicit stacktrace
        stacktrace = traceback.format_exc()
        if not IS_PYTHON3:
            stacktrace = stacktrace.decode("utf-8", "replace")
        log_error("Caught unexpected exception while running test: " + stacktrace)
    end_step(description)


def log_debug(content, step=None):
    """
    Log a debug level message.
    """
    get_runtime().log(LOG_LEVEL_DEBUG, content, step=step)


def log_info(content, step=None):
    """
    Log a info level message.
    """
    get_runtime().log(LOG_LEVEL_INFO, content, step=step)


def log_warning(content, step=None):
    """
    Log a warning level message.
    """
    get_runtime().log(LOG_LEVEL_WARN, content, step=step)


log_warn = log_warning


def log_error(content, step=None):
    """
    Log an error level message.
    """
    get_runtime().log(LOG_LEVEL_ERROR, content, step=step)


def log_check(description, outcome, details=None, step=None):
    get_runtime().log_check(description, outcome, details, step=step)


def prepare_attachment(filename, description=None, step=None):
    """
    Prepare a attachment using a pseudo filename and an optional description.
    The function returns the real filename on disk that will be used by the caller
    to write the attachment content.
    """
    return get_runtime().prepare_attachment(filename, description or filename, step=step)


def save_attachment_file(filename, description=None, step=None):
    """
    Save an attachment using an existing file (identified by filename) and an optional
    description. The given file will be copied.
    """
    get_runtime().save_attachment_file(filename, description or filename, step=step)


def save_attachment_content(content, filename, description=None, binary_mode=False, step=None):
    """
    Save a given content as attachment using pseudo filename and optional description.
    """
    get_runtime().save_attachment_content(content, filename, description or filename, binary_mode, step=step)


def log_url(url, description=None, step=None):
    """
    Log an URL.
    """
    get_runtime().log_url(url, description or url, step=step)


def get_fixture(name):
    """
    Return the corresponding fixture value. Only fixtures whose scope is session_prerun can be retrieved.
    """
    return get_runtime().get_fixture(name)


def add_report_info(name, value):
    report = get_runtime().report
    report.add_info(name, value)


def set_runtime_location(location):
    runtime = get_runtime()
    runtime.location = location
