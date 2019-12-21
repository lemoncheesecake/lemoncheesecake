import os.path as osp
import inspect

from typing import Sequence, Any, List
import six

from lemoncheesecake.helpers.moduleimport import get_matching_files, get_py_files_from_dir, strip_py_ext, import_module
from lemoncheesecake.helpers.introspection import get_object_attributes
from lemoncheesecake.exceptions import UserError, ProgrammingError, ModuleImportError, InvalidMetadataError, \
    InvalidSuiteError, VisibilityConditionNotMet, serialize_current_exception
from lemoncheesecake.suite.core import Test, Suite, SUITE_HOOKS
from lemoncheesecake.testtree import BaseTreeNode
from lemoncheesecake.helpers.typecheck import check_type_string, check_type_dict, check_type


def _is_suite_class(obj):
    return inspect.isclass(obj) and hasattr(obj, "_lccmetadata") and obj._lccmetadata.is_suite


def _is_test_method(obj):
    return inspect.ismethod(obj) and hasattr(obj, "_lccmetadata") and obj._lccmetadata.is_test


def _is_test_function(obj):
    return inspect.isfunction(obj) and hasattr(obj, "_lccmetadata") and obj._lccmetadata.is_test


def _ensure_node_is_visible(obj, metadata):
    if metadata.condition is not None and not metadata.condition(obj):
        raise VisibilityConditionNotMet()


def _check_tags(tags):
    return isinstance(tags, (list, tuple)) and \
           all(isinstance(tag, six.string_types) for tag in tags)


def _check_properties(props):
    return isinstance(props, dict) and \
        all(isinstance(key, six.string_types) for key in props.keys()) and \
        all(isinstance(value, six.string_types) for value in props.values())


def _check_links(links):
    return isinstance(links, (list, tuple)) and \
        all(isinstance(url, six.string_types) for url, _ in links) and \
        all(name is None or isinstance(name, six.string_types) for _, name in links)


def _check_test_tree_node_types(node):
    # type: (BaseTreeNode) -> None
    check_type_string("name", node.name)
    check_type_string("description", node.description)
    check_type("tags", node.tags, "List[str]", _check_tags, show_actual_type=False)
    check_type("properties", node.properties, "Dict[str, str]", _check_properties, show_actual_type=False)
    check_type("links", node.links, "List[Tuple[str, Optional[str]]]", _check_links, show_actual_type=False)


def _load_test(obj):
    md = obj._lccmetadata
    _ensure_node_is_visible(obj, md)

    test = Test(md.name, md.description, obj)
    test.tags.extend(md.tags)
    test.properties.update(md.properties)
    test.links.extend(md.links)
    test.disabled = md.disabled
    test.rank = md.rank
    test.dependencies.extend(md.dependencies)

    try:
        _check_test_tree_node_types(test)
    except TypeError as excp:
        raise InvalidMetadataError("Invalid test metadata for '%s': %s" % (test.name, excp))

    return test


def _load_parametrized_tests(obj):
    md = obj._lccmetadata
    test = _load_test(obj)

    for idx, parameters in enumerate(md.parametrized.parameters_source):
        check_type_dict("test parameters", parameters)
        parametrized_test_name, parametrized_test_description = md.parametrized.naming_scheme(
            test.name, test.description, parameters, idx+1
        )
        parametrized_test = test.pull_node()
        parametrized_test.name = parametrized_test_name
        parametrized_test.description = parametrized_test_description
        parametrized_test.parameters = parameters

        yield parametrized_test


def _load_tests(objs):
    for obj in objs:
        try:
            if obj._lccmetadata.parametrized:
                for test in _load_parametrized_tests(obj):
                    yield test
            else:
                yield _load_test(obj)
        except VisibilityConditionNotMet:
            pass


def _get_test_symbols(obj, filter_func):
    return sorted(
        filter(
            filter_func, (attr for _, attr in get_object_attributes(obj))
        ),
        key=lambda sym: sym._lccmetadata.rank
    )


def _get_test_methods_from_class(obj):
    return _get_test_symbols(obj, _is_test_method)


def _get_sub_suites_from_class(obj):
    return _get_test_symbols(obj, _is_suite_class)


def _get_test_functions_from_module(mod):
    return _get_test_symbols(mod, _is_test_function)


def _get_suite_classes_from_module(mod):
    return _get_test_symbols(mod, _is_suite_class)


def _get_generated_tests(obj):
    return getattr(obj, "_lccgeneratedtests", [])


def load_suite_from_class(class_):
    # type: (Any) -> Suite
    """
    Load a suite from a class.
    """
    try:
        md = class_._lccmetadata
    except AttributeError:
        raise InvalidSuiteError()

    try:
        suite_obj = class_()
    except UserError as e:
        raise e  # propagate UserError
    except Exception:
        raise ProgrammingError("Got an unexpected error while instantiating suite class '%s':%s" % (
            class_.__name__, serialize_current_exception()
        ))
    _ensure_node_is_visible(suite_obj, md)

    suite = Suite(suite_obj, md.name, md.description)
    suite.tags.extend(md.tags)
    suite.properties.update(md.properties)
    suite.links.extend(md.links)
    suite.rank = md.rank
    suite.disabled = md.disabled

    try:
        _check_test_tree_node_types(suite)
    except TypeError as excp:
        raise InvalidMetadataError("Invalid suite metadata for '%s': %s" % (suite.name, excp))

    for hook_name in SUITE_HOOKS:
        if hasattr(suite_obj, hook_name):
            suite.add_hook(hook_name, getattr(suite_obj, hook_name))

    for test in _load_tests(_get_test_methods_from_class(suite_obj)):
        suite.add_test(test)

    for test in _get_generated_tests(suite_obj):
        suite.add_test(test)

    for sub_suite in load_suites_from_classes(_get_sub_suites_from_class(suite_obj)):
        suite.add_suite(sub_suite)

    return suite


def load_suites_from_classes(classes):
    # type: (Sequence[Any]) -> List[Suite]
    """
    Load a list of suites from a list of classes.
    """
    suites = []
    for class_ in classes:
        try:
            suites.append(load_suite_from_class(class_))
        except VisibilityConditionNotMet:
            pass
    return suites


def load_suite_from_module(mod):
    # type: (Any) -> Suite
    """
    Load a suite from a module object.
    """
    # TODO: find a better way to workaround circular import
    from lemoncheesecake.suite.builder import _get_metadata_next_rank

    suite_info = getattr(mod, "SUITE")
    suite_condition = suite_info.get("visible_if")
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
    suite.rank = suite_info.get("rank", _get_metadata_next_rank())

    try:
        _check_test_tree_node_types(suite)
    except TypeError as excp:
        raise InvalidMetadataError("Invalid suite metadata for '%s': %s" % (suite.name, excp))

    for hook_name in SUITE_HOOKS:
        if hasattr(mod, hook_name):
            suite.add_hook(hook_name, getattr(mod, hook_name))

    for test in _load_tests(_get_test_functions_from_module(mod)):
        suite.add_test(test)

    for test in _get_generated_tests(mod):
        suite.add_test(test)

    for sub_suite in load_suites_from_classes(_get_suite_classes_from_module(mod)):
        suite.add_suite(sub_suite)

    return suite


def load_suite_from_file(filename):
    # type: (str) -> Suite

    """
    Load a suite from a Python module indicated by a filename.

    A valid module is either:
      - a module containing a dict name 'SUITE' with keys:
            - description (mandatory)
            - tags (optional)
            - properties (optional)
            - links (optional)
            - rank (optional)

            Example::

                SUITE = {
                    "description": "Such a great test suite"
                }
                @lcc.test("Such a great test")
                def my_test():
                    pass

      - a module that contains a suite class with the same name as the module name

            Example::

                @lcc.suite("Such a great test suite")
                class my_suite:
                    @lcc.test("Such a great test")
                    def my_test():
                        pass

    Raise ModuleImportError if the suite class cannot be imported.
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


def load_suites_from_files(patterns, excluding=()):
    # type: (Sequence[str], Sequence[str]) -> List[Suite]

    """
    Load a list of suites from a list of files.

    :param patterns: a mandatory list (a simple string can also be used instead of a single element list)
      of files to import; the wildcard '*' character can be used
    :param exclude: an optional list (a simple string can also be used instead of a single element list)
      of elements to exclude from the expanded list of files to import

    Example::

        load_suites_from_files("test_*.py")
    """
    suites = []
    for filename in get_matching_files(patterns, excluding):
        try:
            suites.append(load_suite_from_file(filename))
        except VisibilityConditionNotMet:
            pass
    return suites


def load_suites_from_directory(dir, recursive=True):
    # type: (str, bool) -> List[Suite]

    """
    Load a list of suites from a directory.

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
