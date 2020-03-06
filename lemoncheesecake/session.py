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

import six

from lemoncheesecake.consts import ATTACHMENTS_DIR, \
    LOG_LEVEL_DEBUG, LOG_LEVEL_ERROR, LOG_LEVEL_INFO, LOG_LEVEL_WARN
from lemoncheesecake.reporting import Report, ReportLocation
from lemoncheesecake import events
from lemoncheesecake.fixture import ScheduledFixtures
from lemoncheesecake.helpers.typecheck import check_type_string, check_type_bool

_session = None  # type: Optional[Session]

_scheduled_fixtures = None  # type: Optional[ScheduledFixtures]


def _get_thread_id():
    return threading.current_thread().ident


def initialize_session(event_manager, report_dir, report):
    global _session
    _session = Session(event_manager, report_dir, report)
    event_manager.add_listener(_session)


def initialize_fixture_cache(scheduled_fixtures):
    global _scheduled_fixtures
    _scheduled_fixtures = scheduled_fixtures


class _Cursor(object):
    def __init__(self, location, step=None):
        self.location = location
        self.step = step
        self.pending_events = []


class Session(object):
    def __init__(self, event_manager, report_dir, report):
        self.event_manager = event_manager
        self.report_dir = report_dir
        self.report = report
        self.attachments_dir = os.path.join(self.report_dir, ATTACHMENTS_DIR)
        self.attachment_count = 0
        self._attachment_lock = threading.Lock()
        self._failures = set()
        self._local = threading.local()

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

    def end_step(self):
        assert self.cursor.step, "There is no started step"
        self._discard_or_fire_event(
            events.StepStartEvent, events.StepEndEvent(self.cursor.location, self.cursor.step, _get_thread_id())
        )
        self.cursor.step = None

    def _end_step_if_any(self):
        if self.cursor.step:
            self.end_step()

    def log(self, level, content):
        self._flush_pending_events()
        if level == LOG_LEVEL_ERROR:
            self._mark_location_as_failed(self.cursor.location)
        self.event_manager.fire(
            events.LogEvent(self.cursor.location, self.cursor.step, _get_thread_id(), level, content)
        )

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
            attachment_filename = "%04d_%s" % (self.attachment_count + 1, filename)
            self.attachment_count += 1
            if not os.path.exists(self.attachments_dir):
                os.mkdir(self.attachments_dir)

        yield os.path.join(self.attachments_dir, attachment_filename)

        self._flush_pending_events()
        self.event_manager.fire(events.LogAttachmentEvent(
            self.cursor.location, self.cursor.step, _get_thread_id(),
            "%s/%s" % (ATTACHMENTS_DIR, attachment_filename), description, as_image
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


def get_session():
    # type: () -> Session
    assert _session, "Runtime is not initialized"
    return _session


def get_report():
    # type: () -> Report
    report = get_session().report
    assert report, "Report is not available"
    return report


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
    get_session().start_step(description)


def end_step(step):
    """
    Function deprecated since version 1.4.5, does nothing.
    """
    warnings.warn(
        "The 'end_step' function is deprecated since version 1.4.5, it actually does nothing.",
        DeprecationWarning, stacklevel=2
    )


@contextmanager
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


def _log(level, content):
    check_type_string("content", content)
    get_session().log(level, content)


def log_debug(content):
    # type: (str) -> None
    """
    Log a debug level message.
    """
    _log(LOG_LEVEL_DEBUG, content)


def log_info(content):
    # type: (str) -> None
    """
    Log a info level message.
    """
    _log(LOG_LEVEL_INFO, content)


def log_warning(content):
    # type: (str) -> None
    """
    Log a warning level message.
    """
    _log(LOG_LEVEL_WARN, content)


def log_error(content):
    # type: (str) -> None
    """
    Log an error level message.
    """
    _log(LOG_LEVEL_ERROR, content)


def log_check(description, is_successful, details=None):
    check_type_string("description", description)
    check_type_bool("is_successful", is_successful)
    check_type_string("details", details, optional=True)

    get_session().log_check(description, is_successful, details)


def _prepare_attachment(filename, description=None, as_image=False):
    check_type_string("description", description, optional=True)
    check_type_bool("as_image", as_image)

    return get_session().prepare_attachment(filename, description or filename, as_image=as_image)


def prepare_attachment(filename, description=None):
    """
    Context manager. Prepare a attachment using a pseudo filename and an optional description.
    It returns the real filename on disk that will be used by the caller
    to write the attachment content.
    """
    return _prepare_attachment(filename, description)


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


def save_attachment_file(filename, description=None):
    """
    Save an attachment using an existing file (identified by filename) and an optional
    description. The given file will be copied.
    """
    return _save_attachment_file(filename, description)


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


def save_attachment_content(content, filename, description=None):
    """
    Save a given content as attachment using pseudo filename and optional description.
    """
    return _save_attachment_content(content, filename, description, as_image=False)


def save_image_content(content, filename, description=None):
    """
    Save a given image content as attachment using pseudo filename and optional description.
    """
    return _save_attachment_content(content, filename, description, as_image=True)


def log_url(url, description=None):
    # type: (str, Optional[str]) -> None
    """
    Log an URL.
    """
    check_type_string("url", url)
    check_type_string("description", description, optional=True)

    get_session().log_url(url, description or url)


def get_fixture(name):
    """
    Return the corresponding fixture value. Only fixtures whose scope is pre_run can be retrieved.
    """
    global _scheduled_fixtures

    assert _scheduled_fixtures, "Fixture cache has not yet been initialized"
    if not _scheduled_fixtures.has_fixture(name):
        raise LookupError("Fixture '%s' either does not exist or doesn't have a pre_run scope" % name)

    return _scheduled_fixtures.get_fixture_result(name)


def add_report_info(name, value):
    # type: (str, str) -> None

    check_type_string("name", name)
    check_type_string("value", value)

    report = get_report()
    report.add_info(name, value)


def is_location_successful(location):
    return get_session().is_successful(location)


def is_session_successful():
    return get_session().is_successful()


def start_test_session():
    return get_session().start_test_session()


def end_test_session():
    return get_session().end_test_session()


def start_test_session_setup():
    return get_session().start_test_session_setup()


def end_test_session_setup():
    return get_session().end_test_session_setup()


def start_test_session_teardown():
    return get_session().start_test_session_teardown()


def end_test_session_teardown():
    return get_session().end_test_session_teardown()


def start_suite(suite):
    get_session().start_suite(suite)


def end_suite(suite):
    get_session().end_suite(suite)


def start_suite_setup(suite):
    get_session().start_suite_setup(suite)


def end_suite_setup(suite):
    get_session().end_suite_setup(suite)


def start_suite_teardown(suite):
    get_session().start_suite_teardown(suite)


def end_suite_teardown(suite):
    get_session().end_suite_teardown(suite)


def start_test(test):
    get_session().start_test(test)


def end_test(test):
    get_session().end_test(test)


def skip_test(test, reason=None):
    get_session().skip_test(test, reason)


def disable_test(test, reason=None):
    get_session().disable_test(test, reason)


class Thread(threading.Thread):
    """
    Acts exactly as the standard threading.Thread class and must be used instead when running threads
    within a test.
    """
    def __init__(self, *args, **kwargs):
        super(Thread, self).__init__(*args, **kwargs)

        # flush result starting event if any
        session = get_session()
        cursor = session.cursor
        if session.cursor.pending_events and not isinstance(cursor.pending_events[0], events.StepStartEvent):
            event = cursor.pending_events.pop(0)
            session.event_manager.fire(event)

        # keep track of the current location and step
        self._cursor = _Cursor(cursor.location)
        self._default_step = get_session().cursor.step

    def run(self):
        session = get_session()
        session.cursor = self._cursor

        set_step(self._default_step)
        try:
            return super(Thread, self).run()
        except Exception:
            # FIXME: use exception instead of last implicit stacktrace
            stacktrace = traceback.format_exc()
            if six.PY2:
                stacktrace = stacktrace.decode("utf-8", "replace")
            log_error("Caught unexpected exception while running test: " + stacktrace)
        finally:
            session.end_step()
