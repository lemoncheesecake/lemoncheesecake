'''
Created on Mar 18, 2016

@author: nicolas
'''

import os
import sys
import inspect

IS_PYTHON3 = sys.version_info > (3,)
IS_PYTHON2 = sys.version_info < (3,)

def humanize_duration(duration):
    ret = ""

    if duration / 3600 >= 1:
        ret += ("%02dh" if ret else "%dh") % (duration / 3600)
        duration %= 3600

    if duration / 60 >= 1:
        ret += ("%02dm" if ret else "%dm") % (duration / 60)
        duration %= 60

    if duration >= 1:
        ret += ("%02ds" if ret else "%ds") % duration

    if not ret:
        ret = "0s"

    return ret

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

def get_distincts_in_list(lst):
    distincts = []
    for elem in lst:
        if elem not in distincts:
            distincts.append(elem)
    return distincts

def dict_cat(d1, d2):
    new = dict()
    new.update(d1)
    new.update(d2)
    return new
