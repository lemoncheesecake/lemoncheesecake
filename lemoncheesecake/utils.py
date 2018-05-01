'''
Created on Mar 18, 2016

@author: nicolas
'''

import os
import sys
import re
import inspect

IS_PYTHON3 = sys.version_info > (3,)
IS_PYTHON2 = sys.version_info < (3,)


def humanize_duration(duration, show_milliseconds=False):
    ret = ""

    if duration / 3600 >= 1:
        ret += ("%02dh" if ret else "%dh") % (duration / 3600)
        duration %= 3600

    if duration / 60 >= 1:
        ret += ("%02dm" if ret else "%dm") % (duration / 60)
        duration %= 60

    if show_milliseconds:
        if duration >= 0:
            ret += ("%06.03fs" if ret else "%.03fs") % duration
    else:
        if duration >= 1:
            ret += ("%02ds" if ret else "%ds") % duration
        if ret == "":
            ret = "%.03fs" % duration

    return ret


def get_status_color(status):
    if status == "passed":
        return "green"
    elif status == "failed":
        return "red"
    elif status == "disabled":
        return "cyan"
    else:
        return "yellow"


def object_has_method(obj, method_name):
    try:
        return callable(getattr(obj, method_name))
    except AttributeError:
        return False


def get_callable_args(cb):
    spec = inspect.getfullargspec(cb) if IS_PYTHON3 else inspect.getargspec(cb)
    args_start = 1 if inspect.ismethod(cb) else 0
    return spec.args[args_start:]


def get_resource_path(relpath):
    return os.path.join(os.path.dirname(__file__), "resources", relpath)


def dict_cat(d1, d2):
    new = dict()
    new.update(d1)
    new.update(d2)
    return new


def is_string(s):
    if IS_PYTHON2:
        return type(s) in (str, unicode)
    else:
        return type(s) is str


# borrowed from https://stackoverflow.com/a/1176023
def camel_case_to_snake_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
