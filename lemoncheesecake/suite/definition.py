'''
Created on Sep 8, 2016

@author: nicolas
'''

import inspect
import copy

from typing import Any

from lemoncheesecake.suite.core import InjectedFixture, Test, Suite
from lemoncheesecake.exceptions import ProgrammingError


class Metadata(object):
    _next_rank = 1

    def __init__(self):
        self.is_test = False
        self.is_suite = False
        self.name = None
        self.description = None
        self.properties = {}
        self.tags = []
        self.links = []
        self.rank = 0
        self.dependencies = []
        self.disabled = False
        self.condition = None


def _get_metadata_next_rank():
    rank = Metadata._next_rank
    Metadata._next_rank += 1
    return rank


def add_test_into_suite(test, suite):
    # type: (Test, Any) -> None
    """
    Add test into suite

    :param test: a :py:class:`Test <lemoncheesecake.suite.core.Test>` instance
    :param suite: a suite decorated class instance (in that case the function must be
        called when the class is instantiated) or a module marked as a suite (in that case the function
        must be called when the module is loaded)
    """
    if not hasattr(suite, "_lccgeneratedtests"):
        suite._lccgeneratedtests = []
    if test.rank is None:
        test.rank = _get_metadata_next_rank()
    suite._lccgeneratedtests.append(test)


_objects_with_metadata = []
def get_metadata(obj):
    global _objects_with_metadata

    if hasattr(obj, "_lccmetadata"):
        if obj not in _objects_with_metadata:  # metadata comes from the superclass
            obj._lccmetadata = copy.deepcopy(obj._lccmetadata)
        return obj._lccmetadata
    else:
        obj._lccmetadata = Metadata()
        _objects_with_metadata.append(obj)
        return obj._lccmetadata


def suite(description, name=None, rank=None):
    """
    Decorator, mark a class as a suite class.

    :param description: suite's description
    :param name: suite's name (by default, the suite's name is taken from the class's name)
    :param rank: this value is used to order suites of the same hierarchy level
    """
    def wrapper(klass):
        if not inspect.isclass(klass):
            raise ProgrammingError("%s is not a class (suite decorator can only be used on a class)" % klass)
        md = get_metadata(klass)
        if md.dependencies:
            raise ProgrammingError("'depends_on' can not be used on a suite class")
        md.is_suite = True
        md.rank = rank if rank is not None else _get_metadata_next_rank()
        md.name = name or klass.__name__
        md.description = description
        return klass
    return wrapper


def test(description, name=None):
    """
    Decorator, make a method as a test method.

    :param description: test's description
    :param name: test's name (by default, the suite's name is taken from the class's name)
    """
    def wrapper(func):
        if not inspect.isfunction(func):
            raise ProgrammingError("%s is not a function (test decorator can only be used on a function)" % func)
        md = get_metadata(func)
        md.is_test = True
        md.rank = _get_metadata_next_rank()
        md.name = name or func.__name__
        md.description = description
        return func
    return wrapper


def tags(*tag_names):
    """Decorator, add tags to a test or a suite."""
    def wrapper(obj):
        md = get_metadata(obj)
        md.tags.extend(tag_names)
        return obj
    return wrapper


def prop(key, value):
    """Decorator, add a property (key/value) to a test or a suite."""
    def wrapper(obj):
        md = get_metadata(obj)
        md.properties[key] = value
        return obj
    return wrapper


def link(url, name=None):
    """Decorator, set a link (with an optional friendly name) to a test or a suite."""
    def wrapper(obj):
        md = get_metadata(obj)
        md.links.append((url, name))
        return obj
    return wrapper


def disabled():
    """Decorator, mark a test or a suite as disabled, meaning it won't be executed but will be visible
    in report."""
    def wrapper(obj):
        md = get_metadata(obj)
        md.disabled = True
        return obj
    return wrapper


def visible_if(condition):
    """
    Decorator, the test or suite will only appear if the given callable return a true value.

    :param condition: a callable that will take the test object if applied to a test or the suite class
        instance if applied to a suite.
    """
    def wrapper(obj):
        md = get_metadata(obj)
        md.condition = condition
        return obj
    return wrapper


def hidden():
    """Decorator, the test or suite won't be visible in the resulting test tree."""
    return visible_if(lambda _: False)


def depends_on(*deps):
    # type: (*str) -> Any
    """
    Decorator, only applicable to a test. Add dependencies to a test.

    :param deps: the test paths that the decorated test is depending on.
    """
    def wrapper(obj):
        md = get_metadata(obj)
        if md.is_suite:
            raise ProgrammingError("'depends_on' can not be used on a suite class")
        md.dependencies.extend(deps)
        return obj
    return wrapper


def inject_fixture(fixture_name=None):
    """
    Inject a fixture into a suite. If no fixture name is specified then the name of the variable holding
    the injected fixture will be used.
    """
    return InjectedFixture(fixture_name)
