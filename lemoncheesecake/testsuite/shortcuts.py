'''
Created on Sep 8, 2016

@author: nicolas
'''

from lemoncheesecake.runtime import get_runtime

__all__ = "log_debug", "log_info", "log_warn", "log_warning", "log_error", "set_step", \
    "prepare_attachment", "save_attachment_file", "save_attachment_content"

def log_debug(content):
    """
    Log a debug level message.
    """
    get_runtime().log_debug(content)

def log_info(content):
    """
    Log a info level message.
    """
    get_runtime().log_info(content)

def log_warn(content):
    """
    Log a warning level message.
    """
    get_runtime().log_warn(content)

log_warning = log_warn

def log_error(content):
    """
    Log an error level message.
    """
    get_runtime().log_error(content)

def set_step(description):
    """
    Set a new step.
    """
    get_runtime().set_step(description)

def prepare_attachment(filename, description=None):
    """
    Prepare a attachment using a pseudo filename and an optional description.
    The function returns the real filename on disk that will be used by the caller
    to write the attachment content.
    """
    return get_runtime().prepare_attachment(filename, description)

def save_attachment_file(filename, description=None):
    """
    Save an attachment using an existing file (identified by filename) and an optional
    description. The given file will be copied.
    """
    get_runtime().save_attachment_file(filename, description)

def save_attachment_content(content, filename, description=None):
    """
    Save a given content as attachment using pseudo filename and optional description.
    """
    get_runtime().save_attachment_content(content, filename, description)