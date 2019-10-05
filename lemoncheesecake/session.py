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

import six

from lemoncheesecake.consts import ATTACHMENTS_DIR, \
    LOG_LEVEL_DEBUG, LOG_LEVEL_ERROR, LOG_LEVEL_INFO, LOG_LEVEL_WARN
from lemoncheesecake.reporting import Report, ReportLocation
from lemoncheesecake import events
from lemoncheesecake.exceptions import ProgrammingError
from lemoncheesecake.fixture import ScheduledFixtures
from lemoncheesecake.helpers.typecheck import check_type_string, check_type_bool

_session = None  # type: Optional[Session]

_scheduled_fixtures = None  # type: Optional[ScheduledFixtures]


def initialize_session(event_manager, report_dir, report):
    global _session
    _session = Session(event_manager, report_dir, report)
    event_manager.add_listener(_session)


def initialize_fixture_cache(scheduled_fixtures):
    global _scheduled_fixtures
    _scheduled_fixtures = scheduled_fixtures


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
        self._local.location = None
        self._local.step = None

    def set_logging_location(self, location):
        self._local.location = location

    @property
    def location(self):
        return self._local.location

    def mark_location_as_failed(self, location):
        self._failures.add(location)

    def is_successful(self, location=None):
        if location:
            return location not in self._failures
        else:
            return len(self._failures) == 0

    def set_step(self, description, detached=False):
        self._local.step = description
        self.event_manager.fire(events.StepEvent(self._local.location, description, detached=detached))

    def end_step(self, step):
        self.event_manager.fire(events.StepEndEvent(self._local.location, step))

    def log(self, level, content):
        if level == LOG_LEVEL_ERROR:
            self.mark_location_as_failed(self.location)
        self.event_manager.fire(events.LogEvent(self._local.location, self._local.step, level, content))

    def log_check(self, description, is_successful, details):
        if is_successful is False:
            self.mark_location_as_failed(self.location)
        self.event_manager.fire(events.CheckEvent(self._local.location, self._local.step, description, is_successful, details))

    def log_url(self, url, description):
        self.event_manager.fire(events.LogUrlEvent(self._local.location, self._local.step, url, description))

    @contextmanager
    def prepare_attachment(self, filename, description, as_image=False):
        with self._attachment_lock:
            attachment_filename = "%04d_%s" % (self.attachment_count + 1, filename)
            self.attachment_count += 1
            if not os.path.exists(self.attachments_dir):
                os.mkdir(self.attachments_dir)

        yield os.path.join(self.attachments_dir, attachment_filename)

        self.event_manager.fire(events.LogAttachmentEvent(
            self._local.location, self._local.step, "%s/%s" % (ATTACHMENTS_DIR, attachment_filename),
            description, as_image
        ))

    def start_test_session(self):
        self.event_manager.fire(events.TestSessionStartEvent(self.report))

    def end_test_session(self):
        self.event_manager.fire(events.TestSessionEndEvent(self.report))

    def start_test_session_setup(self):
        self.event_manager.fire(events.TestSessionSetupStartEvent())
        self.set_logging_location(ReportLocation.in_test_session_setup())

    def end_test_session_setup(self):
        self.event_manager.fire(events.TestSessionSetupEndEvent())

    def start_test_session_teardown(self):
        self.event_manager.fire(events.TestSessionTeardownStartEvent())
        self.set_logging_location(ReportLocation.in_test_session_teardown())

    def end_test_session_teardown(self):
        self.event_manager.fire(events.TestSessionTeardownEndEvent())

    def start_suite(self, suite):
        self.event_manager.fire(events.SuiteStartEvent(suite))

    def end_suite(self, suite):
        self.event_manager.fire(events.SuiteEndEvent(suite))

    def start_suite_setup(self, suite):
        self.event_manager.fire(events.SuiteSetupStartEvent(suite))
        self.set_logging_location(ReportLocation.in_suite_setup(suite))

    def end_suite_setup(self, suite):
        self.event_manager.fire(events.SuiteSetupEndEvent(suite))

    def start_suite_teardown(self, suite):
        self.event_manager.fire(events.SuiteTeardownStartEvent(suite))
        self.set_logging_location(ReportLocation.in_suite_teardown(suite))

    def end_suite_teardown(self, suite):
        self.event_manager.fire(events.SuiteTeardownEndEvent(suite))

    def start_test(self, test):
        self.event_manager.fire(events.TestStartEvent(test))
        self.set_logging_location(ReportLocation.in_test(test))

    def end_test(self, test):
        self.event_manager.fire(events.TestEndEvent(test))

    def skip_test(self, test, reason):
        self.event_manager.fire(events.TestSkippedEvent(test, reason))
        self.mark_location_as_failed(ReportLocation.in_test(test))

    def disable_test(self, test, reason):
        self.event_manager.fire(events.TestDisabledEvent(test, reason))


def get_session():
    # type: () -> Session
    if not _session:
        raise ProgrammingError("Runtime is not initialized")
    return _session


def get_report():
    # type: () -> Report
    report = get_session().report
    if not report:
        raise ProgrammingError("Report is not available")
    return report


def set_step(description, detached=False):
    # type: (str, bool) -> None
    """
    Set a new step.

    :param description: the step description
    :param detached: whether or not the step is "detached"
    """
    check_type_string("description", description)
    get_session().set_step(description, detached=detached)


def end_step(step):
    """
    End a detached step.
    """
    get_session().end_step(step)


@contextmanager
def detached_step(description):
    """
    Context manager. Like set_step, but ends the step at the end of the "with" block.
    Intended to be use with code run through lcc.Thread.
    """
    set_step(description, detached=True)
    try:
        yield
    except Exception:
        # FIXME: use exception instead of last implicit stacktrace
        stacktrace = traceback.format_exc()
        if six.PY2:
            stacktrace = stacktrace.decode("utf-8", "replace")
        log_error("Caught unexpected exception while running test: " + stacktrace)
    end_step(description)


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

    if not _scheduled_fixtures:
        raise ProgrammingError("Fixture cache has not yet been initialized")

    if not _scheduled_fixtures.has_fixture(name):
        raise ProgrammingError("Fixture '%s' either does not exist or don't have a prerun_session scope" % name)

    try:
        return _scheduled_fixtures.get_fixture_result(name)
    except AssertionError as excp:
        raise ProgrammingError(str(excp))


def add_report_info(name, value):
    # type: (str, str) -> None

    check_type_string("name", name)
    check_type_string("value", value)

    report = get_report()
    report.add_info(name, value)


def set_session_location(location):
    get_session().set_logging_location(location)


def mark_location_as_failed(location):
    get_session().mark_location_as_failed(location)


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
        self.location = get_session().location

    def run(self):
        set_session_location(self.location)
        return super(Thread, self).run()
