'''
Created on Jan 24, 2016

@author: nicolas
'''

import os.path
import shutil

from lemoncheesecake.exceptions import LemonCheesecakeInternalError
from lemoncheesecake.consts import ATTACHEMENT_DIR, \
    LOG_LEVEL_DEBUG, LOG_LEVEL_ERROR, LOG_LEVEL_INFO, LOG_LEVEL_WARN
from lemoncheesecake.reporting import *
from lemoncheesecake import events

__all__ = "log_debug", "log_info", "log_warn", "log_warning", "log_error", "log_url", "log_check", \
    "set_step", "prepare_attachment", "save_attachment_file", "save_attachment_content", \
    "add_report_info"


_runtime = None  # singleton


def initialize_runtime(report_dir, report):
    global _runtime
    _runtime = _Runtime(report_dir, report)
    events.add_listener(_runtime)


def get_runtime():
    if not _runtime:
        raise LemonCheesecakeInternalError("Runtime is not initialized")
    return _runtime


class _Runtime:
    def __init__(self, report_dir, report):
        self.report_dir = report_dir
        self.report = report
        self.attachments_dir = os.path.join(self.report_dir, ATTACHEMENT_DIR)
        self.attachment_count = 0
        self.step_lock = False

    def set_step(self, description, force_lock):
        if self.step_lock and not force_lock:
            return

        events.fire("on_step", description)

    def log(self, level, content):
        events.fire("on_log", level, content)

    def log_check(self, description, outcome, details):
        events.fire("on_check", description, outcome, details)

    def log_url(self, url, description):
        events.fire("on_log_url", url, description)

    def prepare_attachment(self, filename, description):
        attachment_filename = "%04d_%s" % (self.attachment_count + 1, filename)
        self.attachment_count += 1
        if not os.path.exists(self.attachments_dir):
            os.mkdir(self.attachments_dir)

        events.fire("on_log_attachment", "%s/%s" % (ATTACHEMENT_DIR, attachment_filename), description)

        return os.path.join(self.attachments_dir, attachment_filename)

    def save_attachment_file(self, filename, description):
        target_filename = self.prepare_attachment(os.path.basename(filename), description)
        shutil.copy(filename, target_filename)

    def save_attachment_content(self, content, filename, description, binary_mode):
        target_filename = self.prepare_attachment(filename, description)

        fh = open(target_filename, "wb")
        fh.write(content if binary_mode else content.encode("utf-8"))
        fh.close()


def log_debug(content):
    """
    Log a debug level message.
    """
    get_runtime().log(LOG_LEVEL_DEBUG, content)


def log_info(content):
    """
    Log a info level message.
    """
    get_runtime().log(LOG_LEVEL_INFO, content)


def log_warning(content):
    """
    Log a warning level message.
    """
    get_runtime().log(LOG_LEVEL_WARN, content)

log_warn = log_warning


def log_error(content):
    """
    Log an error level message.
    """
    get_runtime().log(LOG_LEVEL_ERROR, content)


def log_check(description, outcome, details=None):
    get_runtime().log_check(description, outcome, details)


def set_step(description, force_lock=False):
    """
    Set a new step.
    """
    get_runtime().set_step(description, force_lock)


def prepare_attachment(filename, description=None):
    """
    Prepare a attachment using a pseudo filename and an optional description.
    The function returns the real filename on disk that will be used by the caller
    to write the attachment content.
    """
    return get_runtime().prepare_attachment(filename, description or filename)


def save_attachment_file(filename, description=None):
    """
    Save an attachment using an existing file (identified by filename) and an optional
    description. The given file will be copied.
    """
    get_runtime().save_attachment_file(filename, description or filename)


def save_attachment_content(content, filename, description=None, binary_mode=False):
    """
    Save a given content as attachment using pseudo filename and optional description.
    """
    get_runtime().save_attachment_content(content, filename, description or filename, binary_mode)


def log_url(url, description=None):
    """
    Log an URL.
    """
    get_runtime().log_url(url, description or url)


def add_report_info(name, value):
    report = get_runtime().report
    report.add_info(name, value)
