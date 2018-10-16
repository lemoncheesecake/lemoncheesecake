'''
Created on Mar 18, 2016

@author: nicolas
'''

import os
import sys
import re
import inspect
import collections

from lemoncheesecake.exceptions import ProgrammingError

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
    if not inspect.isroutine(cb):
        try:
            cb = getattr(cb, "__call__")
        except AttributeError:
            raise ProgrammingError("%s is not something that can be called" % cb)

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


###
# OrderedSet, by Raymond Hettinger
# see http://code.activestate.com/recipes/576694-orderedset/
##

class OrderedSet(collections.MutableSet):

    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]  # sentinel node for doubly linked list
        self.map = {}  # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def update(self, other):  # the update method is the only modification to the original class
        self |= other

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)
