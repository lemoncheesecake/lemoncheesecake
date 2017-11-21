'''
Created on Feb 5, 2017

@author: nicolas
'''

import os.path as osp
import inspect

from lemoncheesecake.importer import get_matching_files, get_py_files_from_dir, strip_py_ext, import_module
from lemoncheesecake.exceptions import UserError, ProgrammingError, ModuleImportError, InvalidMetadataError, \
    InvalidSuiteError, VisibilityConditionNotMet, serialize_current_exception
from lemoncheesecake.suite.core import Test, Suite, SUITE_HOOKS

__all__ = "load_suite_from_file", "load_suites_from_files", "load_suites_from_directory", \
    "load_suite_from_class", "load_suites_from_classes"


def is_suite_class(obj):
    return inspect.isclass(obj) and hasattr(obj, "_lccmetadata") and obj._lccmetadata.is_suite


def is_test_method(obj):
    return inspect.ismethod(obj) and hasattr(obj, "_lccmetadata") and obj._lccmetadata.is_test


def is_test_function(obj):
    return inspect.isfunction(obj) and hasattr(obj, "_lccmetadata") and obj._lccmetadata.is_test


def ensure_node_is_visible(obj, metadata):
    if metadata.condition is not None and not metadata.condition(obj):
        raise VisibilityConditionNotMet()


def load_test(obj):
    md = obj._lccmetadata
    ensure_node_is_visible(obj, md)

    test = Test(md.name, md.description, obj)
    test.tags.extend(md.tags)
    test.properties.update(md.properties)
    test.links.extend(md.links)
    test.disabled = md.disabled
    return test


def load_test_from_method(method):
    return load_test(method)


def load_test_from_function(func):
    return load_test(func)


def load_tests(objs):
    tests = []
    for obj in objs:
        try:
            tests.append(load_test(obj))
        except VisibilityConditionNotMet:
            pass
    return tests


def load_tests_from_methods(methods):
    return load_tests(methods)


def load_tests_from_functions(funcs):
    return load_tests(funcs)


def _list_object_attributes(obj):
    return [getattr(obj, n) for n in dir(obj) if not n.startswith("__")]


def get_test_methods_from_class(obj):
    return sorted(filter(is_test_method, _list_object_attributes(obj)), key=lambda m: m._lccmetadata.rank)


def get_sub_suites_from_class(obj):
    return sorted(filter(is_suite_class, _list_object_attributes(obj)), key=lambda c: c._lccmetadata.rank)


def get_test_functions_from_module(mod):
    return filter(is_test_function, _list_object_attributes(mod))


def get_suite_classes_from_module(mod):
    return filter(is_suite_class, _list_object_attributes(mod))


def load_suite_from_class(class_):
    try:
        md = class_._lccmetadata
    except AttributeError:
        raise InvalidSuiteError()

    try:
        suite_obj = class_()
    except UserError as e:
        raise e # propagate UserError
    except Exception:
        raise ProgrammingError("Got an unexpected error while instantiating suite class '%s':%s" % (
            class_.__name__, serialize_current_exception()
        ))
    ensure_node_is_visible(suite_obj, md)

    suite = Suite(suite_obj, md.name, md.description)
    suite.tags.extend(md.tags)
    suite.properties.update(md.properties)
    suite.links.extend(md.links)
    suite.rank = md.rank
    suite.disabled = md.disabled

    for hook_name in SUITE_HOOKS:
        if hasattr(suite_obj, hook_name):
            suite.add_hook(hook_name, getattr(suite_obj, hook_name))

    for test in load_tests_from_methods(get_test_methods_from_class(suite_obj)):
        suite.add_test(test)

    for sub_suite in load_suites_from_classes(get_sub_suites_from_class(suite_obj)):
        suite.add_suite(sub_suite)

    return suite


def load_suites_from_classes(classes):
    suites = []
    for class_ in classes:
        try:
            suites.append(load_suite_from_class(class_))
        except VisibilityConditionNotMet:
            pass
    return suites


def load_suite_from_module(mod):
    # TODO: find a better way to workaround circular import
    from lemoncheesecake.suite.definition import get_metadata_next_rank

    suite_info = getattr(mod, "SUITE")
    suite_condition = suite_info.get("conditional")
    if suite_condition is not None and not suite_condition(mod):
        raise VisibilityConditionNotMet()

    suite_name = inspect.getmodulename(inspect.getfile(mod))

    try:
        suite_description = suite_info["description"]
    except KeyError:
        raise InvalidMetadataError("Missing description in '%s' suite information" % mod.__file__)

    suite = Suite(mod, suite_name, suite_description)
    suite.tags.extend(suite_info.get("tags", []))
    suite.properties.update(suite_info.get("properties", []))
    suite.links.extend(suite_info.get("links", []))
    suite.rank = suite_info.get("rank", get_metadata_next_rank())

    for hook_name in SUITE_HOOKS:
        if hasattr(mod, hook_name):
            suite.add_hook(hook_name, getattr(mod, hook_name))

    for test in load_tests_from_functions(get_test_functions_from_module(mod)):
        suite.add_test(test)

    sub_suites = []
    for sub_suite in load_suites_from_classes(get_suite_classes_from_module(mod)):
        sub_suites.append(sub_suite)
    sub_suites.sort(key=lambda suite: suite.rank)
    for sub_suite in sub_suites:
        suite.add_suite(sub_suite)

    return suite


def load_suite_from_file(filename):
    """Get suite from Python module.

    A valid module is either:
    - a module containing a dict name 'SUITE' with keys:
      - description (mandatory)
      - tags (optional)
      - properties (optional)
      - links (optional)
      - rank (optional)
    - a module that contains a suite class with the same name as the module name

    Raise a ModuleImportError if the suite class cannot be imported.
    """
    mod = import_module(filename)

    if hasattr(mod, "SUITE"):
        suite = load_suite_from_module(mod)
    else:
        mod_name = strip_py_ext(osp.basename(filename))
        try:
            klass = getattr(mod, mod_name)
        except AttributeError:
            raise ModuleImportError("Cannot find class '%s' in '%s'" % (mod_name, mod.__file__))

        suite = load_suite_from_class(klass)
    return suite


def load_suites_from_files(patterns, excluding=[]):
    """
    Import suites from a list of files:
    - patterns: a mandatory list (a simple string can also be used instead of a single element list)
      of files to import; the wildcard '*' character can be used
    - exclude: an optional list (a simple string can also be used instead of a single element list)
      of elements to exclude from the expanded list of files to import
    Example: load_suites_from_files("test_*.py")
    """
    suites = []
    for filename in get_matching_files(patterns, excluding):
        try:
            suites.append(load_suite_from_file(filename))
        except VisibilityConditionNotMet:
            pass
    return suites


def load_suites_from_directory(dir, recursive=True):
    """Find suite classes in modules found in dir.

    The function expect that:
    - each module (.py file) contains a class that inherits Suite
    - the class name must have the same name as the module name (if the module is foo.py
      the class must be named foo)
    If the recursive argument is set to True, sub suites will be searched in a directory named
    from the suite module: if the suite module is "foo.py" then the sub suites directory must be "foo".

    Raise ModuleImportError if one or more suite cannot be imported.
    """
    if not osp.exists(dir):
        raise ModuleImportError("Directory '%s' does not exist" % dir)

    suites = []
    for filename in get_py_files_from_dir(dir):
        try:
            suite = load_suite_from_file(filename)
        except VisibilityConditionNotMet:
            continue

        if recursive:
            subsuites_dir = strip_py_ext(filename)
            if osp.isdir(subsuites_dir):
                for sub_suite in load_suites_from_directory(subsuites_dir, recursive=True):
                    suite.add_suite(sub_suite)
        suites.append(suite)
    suites.sort(key=lambda suite: suite.rank)
    return suites
