'''
Created on Jan 24, 2016

@author: nicolas
'''

import os.path
from contextlib import contextmanager
import shutil
import threading
import traceback
from typing import Optional
import warnings
import functools

import six

from lemoncheesecake.reporting import Report, ReportWriter, ReportLocation, Log
from lemoncheesecake import events
from lemoncheesecake.helpers.typecheck import check_type_string, check_type_bool
from lemoncheesecake.exceptions import AbortTest

_ATTACHMENTS_DIR = "attachments"


def _get_thread_id():
    return threading.current_thread().ident


class _Cursor(object):
    def __init__(self, location, step=None):
        self.location = location
        self.step = step
        self.pending_events = []


class Session(object):
    _instance = None

    def __init__(self, event_manager, report_dir, report):
        self.event_manager = event_manager
        self.report_dir = report_dir
        self.report = report
        self.aborted = False
        self._attachments_dir = os.path.join(self.report_dir, _ATTACHMENTS_DIR)
        self._attachment_count = 0
        self._attachment_lock = threading.Lock()
        self._failures = set()
        self._local = threading.local()

    @classmethod
    def create(cls, event_manager, reporting_backends, report_dir, report_saving_strategy,
               nb_threads=1, parallelized=None):
        report = Report()
        report.nb_threads = nb_threads
        event_manager.add_listener(ReportWriter(report))

        cls._instance = cls(event_manager, report_dir, report)

        # hint: tests with nb_threads > 1 are not actually parallelized if there is only one test
        # that's why there is a dedicated parallelized argument alongside nb_threads
        if parallelized is None:
            parallelized = nb_threads > 1

        for backend in reporting_backends:
            event_manager.add_listener(
                backend.create_reporting_session(report_dir, report, parallelized, report_saving_strategy)
            )

        return cls._instance

    @classmethod
    def get(cls):
        assert cls._instance, "Session has not been created (yet)"
        return cls._instance

    @property
    def cursor(self):  # type: () -> _Cursor
        return self._local.cursor

    @cursor.setter
    def cursor(self, cursor):
        self._local.cursor = cursor

    def _hold_event(self, event):
        self.cursor.pending_events.append(event)

    def _flush_pending_events(self):
        for event in self.cursor.pending_events:
            self.event_manager.fire(event)
        del self.cursor.pending_events[:]

    def _discard_pending_event_if_any(self, event_class):
        if self.cursor.pending_events and isinstance(self.cursor.pending_events[-1], event_class):
            self.cursor.pending_events.pop()
            return True
        else:
            return False

    def _discard_or_fire_event(self, event_class, event):
        discarded = self._discard_pending_event_if_any(event_class)
        if not discarded:
            self.event_manager.fire(event)

    def _mark_location_as_failed(self, location):
        self._failures.add(location)

    def is_successful(self, location=None):
        if location:
            return location not in self._failures
        else:
            return len(self._failures) == 0

    def start_step(self, description):
        self._end_step_if_any()
        self.cursor.step = description
        self._hold_event(
            events.StepStartEvent(self.cursor.location, description, _get_thread_id())
        )
    set_step = start_step

    def end_step(self):
        assert self.cursor.step, "There is no started step"
        self._discard_or_fire_event(
            events.StepStartEvent, events.StepEndEvent(self.cursor.location, self.cursor.step, _get_thread_id())
        )
        self.cursor.step = None

    def _end_step_if_any(self):
        if self.cursor.step:
            self.end_step()

    def _log(self, level, content):
        self._flush_pending_events()
        if level == Log.LEVEL_ERROR:
            self._mark_location_as_failed(self.cursor.location)
        self.event_manager.fire(
            events.LogEvent(self.cursor.location, self.cursor.step, _get_thread_id(), level, content)
        )

    def log_debug(self, content):
        return self._log(Log.LEVEL_DEBUG, content)

    def log_info(self, content):
        return self._log(Log.LEVEL_INFO, content)

    def log_warning(self, content):
        return self._log(Log.LEVEL_WARN, content)

    def log_error(self, content):
        return self._log(Log.LEVEL_ERROR, content)

    def log_check(self, description, is_successful, details):
        self._flush_pending_events()
        if is_successful is False:
            self._mark_location_as_failed(self.cursor.location)
        self.event_manager.fire(events.CheckEvent(
            self.cursor.location, self.cursor.step, _get_thread_id(), description, is_successful, details
        ))

    def log_url(self, url, description):
        self._flush_pending_events()
        self.event_manager.fire(
            events.LogUrlEvent(self.cursor.location, self.cursor.step, _get_thread_id(), url, description)
        )

    @contextmanager
    def prepare_attachment(self, filename, description, as_image=False):
        with self._attachment_lock:
            attachment_filename = "%04d_%s" % (self._attachment_count + 1, filename)
            self._attachment_count += 1
            if not os.path.exists(self._attachments_dir):
                os.mkdir(self._attachments_dir)

        yield os.path.join(self._attachments_dir, attachment_filename)

        self._flush_pending_events()
        self.event_manager.fire(events.LogAttachmentEvent(
            self.cursor.location, self.cursor.step, _get_thread_id(),
            "%s/%s" % (_ATTACHMENTS_DIR, attachment_filename), description, as_image
        ))

    def start_test_session(self):
        self.event_manager.fire(events.TestSessionStartEvent(self.report))

    def end_test_session(self):
        self.event_manager.fire(events.TestSessionEndEvent(self.report))

    def start_test_session_setup(self):
        self.cursor = _Cursor(ReportLocation.in_test_session_setup())
        self._hold_event(events.TestSessionSetupStartEvent())

    def end_test_session_setup(self):
        self._end_step_if_any()
        self._discard_or_fire_event(events.TestSessionSetupStartEvent, events.TestSessionSetupEndEvent())

    def start_test_session_teardown(self):
        self.cursor = _Cursor(ReportLocation.in_test_session_teardown())
        self._hold_event(events.TestSessionTeardownStartEvent())

    def end_test_session_teardown(self):
        self._end_step_if_any()
        self._discard_or_fire_event(events.TestSessionTeardownStartEvent, events.TestSessionTeardownEndEvent())

    def start_suite(self, suite):
        self.event_manager.fire(events.SuiteStartEvent(suite))

    def end_suite(self, suite):
        self.event_manager.fire(events.SuiteEndEvent(suite))

    def start_suite_setup(self, suite):
        self.cursor = _Cursor(ReportLocation.in_suite_setup(suite))
        self._hold_event(events.SuiteSetupStartEvent(suite))

    def end_suite_setup(self, suite):
        self._end_step_if_any()
        self._discard_or_fire_event(events.SuiteSetupStartEvent, events.SuiteSetupEndEvent(suite))

    def start_suite_teardown(self, suite):
        self.cursor = _Cursor(ReportLocation.in_suite_teardown(suite))
        self._hold_event(events.SuiteTeardownStartEvent(suite))

    def end_suite_teardown(self, suite):
        self._end_step_if_any()
        self._discard_or_fire_event(events.SuiteTeardownStartEvent, events.SuiteTeardownEndEvent(suite))

    def start_test(self, test):
        self.event_manager.fire(events.TestStartEvent(test))
        self.cursor = _Cursor(ReportLocation.in_test(test))

    def end_test(self, test):
        self._end_step_if_any()
        self.event_manager.fire(events.TestEndEvent(test))

    def skip_test(self, test, reason):
        self.event_manager.fire(events.TestSkippedEvent(test, reason))
        self._mark_location_as_failed(ReportLocation.in_test(test))

    def disable_test(self, test, reason):
        self.event_manager.fire(events.TestDisabledEvent(test, reason))


def _interruptible(wrapped):
    @functools.wraps(wrapped)
    def wrapper(*args, **kwargs):
        if Session.get().aborted:
            raise AbortTest("tests have been manually stopped")
        return wrapped(*args, **kwargs)
    wrapper.__doc__ = wrapped.__doc__
    return wrapper


@_interruptible
def set_step(description, detached=NotImplemented):
    # type: (str, bool) -> None
    """
    Set a new step.

    :param description: the step description
    :param detached: argument deprecated since 1.4.5, does nothing.
    """
    if detached is not NotImplemented:
        warnings.warn(
            "The 'detached' argument does no longer do anything (deprecated since version 1.4.5)",
            DeprecationWarning, stacklevel=2
        )

    check_type_string("description", description)
    Session.get().start_step(description)


def end_step(step):
    """
    Function deprecated since version 1.4.5, does nothing.
    """
    warnings.warn(
        "The 'end_step' function is deprecated since version 1.4.5, it actually does nothing.",
        DeprecationWarning, stacklevel=2
    )


@contextmanager
@_interruptible
def detached_step(description):
    """
    Context manager deprecated since version 1.4.5, it only does a set_step.
    """
    warnings.warn(
        "The 'detached_step' context manager is deprecated since version 1.4.5. Use 'set_step' function instead.",
        DeprecationWarning, stacklevel=2
    )
    set_step(description)
    yield


@_interruptible
def log_debug(content):
    # type: (str) -> None
    """
    Log a debug level message.
    """
    check_type_string("content", content)
    Session.get().log_debug(content)


@_interruptible
def log_info(content):
    # type: (str) -> None
    """
    Log a info level message.
    """
    check_type_string("content", content)
    Session.get().log_info(content)


@_interruptible
def log_warning(content):
    # type: (str) -> None
    """
    Log a warning level message.
    """
    check_type_string("content", content)
    Session.get().log_warning(content)


@_interruptible
def log_error(content):
    # type: (str) -> None
    """
    Log an error level message.
    """
    check_type_string("content", content)
    Session.get().log_error(content)


@_interruptible
def log_check(description, is_successful, details=None):
    check_type_string("description", description)
    check_type_bool("is_successful", is_successful)
    check_type_string("details", details, optional=True)

    Session.get().log_check(description, is_successful, details)


def _prepare_attachment(filename, description=None, as_image=False):
    check_type_string("description", description, optional=True)
    check_type_bool("as_image", as_image)

    return Session.get().prepare_attachment(filename, description or filename, as_image=as_image)


@_interruptible
def prepare_attachment(filename, description=None):
    """
    Context manager. Prepare a attachment using a pseudo filename and an optional description.
    It returns the real filename on disk that will be used by the caller
    to write the attachment content.
    """
    return _prepare_attachment(filename, description)


@_interruptible
def prepare_image_attachment(filename, description=None):
    """
    Context manager. Prepare an image attachment using a pseudo filename and an optional description.
    The function returns the real filename on disk that will be used by the caller
    to write the attachment content.
    """
    return _prepare_attachment(filename, description, as_image=True)


def _save_attachment_file(filename, description=None, as_image=False):
    with _prepare_attachment(os.path.basename(filename), description, as_image=as_image) as report_attachment_path:
        shutil.copy(filename, report_attachment_path)


@_interruptible
def save_attachment_file(filename, description=None):
    """
    Save an attachment using an existing file (identified by filename) and an optional
    description. The given file will be copied.
    """
    return _save_attachment_file(filename, description)


@_interruptible
def save_image_file(filename, description=None):
    """
    Save an image using an existing file (identified by filename) and an optional
    description. The given file will be copied.
    """
    return _save_attachment_file(filename, description, as_image=True)


def _save_attachment_content(content, filename, description=None, as_image=False):
    if type(content) is six.text_type:
        opening_mode = "w"
        if six.PY2:
            content = content.encode("utf-8")
    else:
        opening_mode = "wb"

    with _prepare_attachment(filename, description, as_image=as_image) as path:
        with open(path, opening_mode) as fh:
            fh.write(content)


@_interruptible
def save_attachment_content(content, filename, description=None):
    """
    Save a given content as attachment using pseudo filename and optional description.
    """
    return _save_attachment_content(content, filename, description, as_image=False)


@_interruptible
def save_image_content(content, filename, description=None):
    """
    Save a given image content as attachment using pseudo filename and optional description.
    """
    return _save_attachment_content(content, filename, description, as_image=True)


@_interruptible
def log_url(url, description=None):
    # type: (str, Optional[str]) -> None
    """
    Log an URL.
    """
    check_type_string("url", url)
    check_type_string("description", description, optional=True)

    Session.get().log_url(url, description or url)


def add_report_info(name, value):
    # type: (str, str) -> None

    check_type_string("name", name)
    check_type_string("value", value)

    session = Session.get()
    session.report.add_info(name, value)


class Thread(threading.Thread):
    """
    Acts exactly as the standard threading.Thread class and must be used instead when running threads
    within a test.
    """
    def __init__(self, *args, **kwargs):
        super(Thread, self).__init__(*args, **kwargs)
        self._session = Session.get()

        # flush result starting event if any
        cursor = self._session.cursor
        if self._session.cursor.pending_events and not isinstance(cursor.pending_events[0], events.StepStartEvent):
            event = cursor.pending_events.pop(0)
            self._session.event_manager.fire(event)

        # keep track of the current location and step
        self._cursor = _Cursor(cursor.location)
        self._default_step = self._session.cursor.step

    def run(self):
        self._session.cursor = self._cursor
        self._session.start_step(self._default_step)
        try:
            return super(Thread, self).run()
        except Exception:
            # FIXME: use exception instead of last implicit stacktrace
            stacktrace = traceback.format_exc()
            if six.PY2:
                stacktrace = stacktrace.decode("utf-8", "replace")
            log_error("Caught unexpected exception while running test: " + stacktrace)
        finally:
            self._session.end_step()
