'''
Created on Sep 8, 2016

@author: nicolas
'''

import inspect
import copy

from typing import Any, Iterable, Callable, Optional, Tuple, Sequence, Union

from lemoncheesecake.helpers.text import STRING_TYPES
from lemoncheesecake.suite.core import InjectedFixture, Test


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
        self.parametrized = None


def _get_metadata_next_rank():
    rank = Metadata._next_rank
    Metadata._next_rank += 1
    return rank


def build_description_from_name(name):
    return name.capitalize().replace("_", " ")


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


def suite(description=None, name=None, rank=None):
    """
    Decorator, mark a class as a suite class.

    :param description: suite's description (by default, the suite's description is built from the name)
    :param name: suite's name (by default, the suite's name is taken from the class's name)
    :param rank: this value is used to order suites of the same hierarchy level
    """
    def wrapper(klass):
        assert inspect.isclass(klass), "%s is not a class (suite decorator can only be used on a class)" % klass
        md = get_metadata(klass)
        assert not md.dependencies, "'depends_on' can not be used on a suite class"
        md.is_suite = True
        md.rank = rank if rank is not None else _get_metadata_next_rank()
        md.name = name or klass.__name__
        md.description = description or build_description_from_name(md.name)
        return klass
    return wrapper


def test(description=None, name=None):
    """
    Decorator, mark a function/method as a test.

    :param description: test's description
    :param name: test's name (by default, the suite's name is taken from the class's name)
    """
    def wrapper(func):
        assert inspect.isfunction(func), "%s is not a function (test decorator can only be used on a function)" % func
        md = get_metadata(func)
        md.is_test = True
        md.rank = _get_metadata_next_rank()
        md.name = name or func.__name__
        md.description = description or build_description_from_name(md.name)
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


def disabled(reason=None):
    """Decorator, mark a test or a suite as disabled, meaning it won't be executed but will be visible
    in report. An optional reason can be passed to the decorator (*new in version 1.1.0*)."""
    def wrapper(obj):
        md = get_metadata(obj)
        md.disabled = reason if reason else True
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
        assert not md.is_suite, "'depends_on' can only be used on a test, not on a suite"
        md.dependencies.extend(deps)
        return obj
    return wrapper


def inject_fixture(fixture_name=None):
    """
    Inject a fixture into a suite. If no fixture name is specified then the name of the variable holding
    the injected fixture will be used.
    """
    return InjectedFixture(fixture_name)


def _default_naming_scheme(name, description, parameters, nb):
    return name + "_%d" % nb, description + " #%d" % nb


def _format_naming_scheme(name_fmt, description_fmt):
    def naming_scheme(_, __, parameters, ___):
        return name_fmt.format(**parameters), description_fmt.format(**parameters)
    return naming_scheme


class _Parametrized(object):
    def __init__(self, parameters_source, naming_scheme):
        self._parameters_source = parameters_source
        self.naming_scheme = naming_scheme

    @property
    def parameters_source(self):
        source = iter(self._parameters_source)
        try:
            first_item = next(source)
        except StopIteration:
            return
        if type(first_item) is dict:
            yield first_item
            for item in source:
                yield item
        else:
            if type(first_item) in STRING_TYPES:
                names = [s.strip() for s in first_item.split(",")]
            else:
                names = first_item  # assume list or tuple
            for values in source:
                yield dict(zip(names, values))


def parametrized(parameter_source, naming_scheme=_default_naming_scheme):
    # type: (Iterable, Optional[Union[Callable[[str, str, dict, int], Tuple[str, str]], Sequence]]) -> Any
    """
    Decorator, make the test parametrized.

    :param parameter_source: it can be either:

        -  an iterable of dicts, each dict representing the arguments passed to the test

        - a CSV-like mode, where the first element of the list represents the argument names as an str or a sequence
          (example: ``"i,j"`` or ``("i", "j")``) and the remaining elements are sequences of the arguments to be
          passed to the test.

    :param naming_scheme: optional, it can be either:

      - a optional function that takes as parameters the base test name, description, parameters, index
        and must return the expanded test name and description as a two elements list

      - a tuple/list of two (name + description) format strings, example: ``("test_{i}_plus_{j}", "Test {i} plus {j}")``
    """

    def wrapper(obj):
        md = get_metadata(obj)
        md.parametrized = _Parametrized(
            parameter_source,
            naming_scheme if callable(naming_scheme) else _format_naming_scheme(*naming_scheme)
        )
        return obj
    return wrapper
