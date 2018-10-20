'''
Created on Mar 18, 2016

@author: nicolas
'''

import os
import sys
import re

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


def get_resource_path(relpath):
    return os.path.join(os.path.dirname(__file__), "resources", relpath)


# borrowed from https://stackoverflow.com/a/1176023
def camel_case_to_snake_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
