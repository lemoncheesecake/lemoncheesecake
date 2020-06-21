import os
import os.path as osp
import inspect

from typing import Sequence, Any, List
import six

from lemoncheesecake.helpers.moduleimport import get_matching_files, get_py_files_from_dir, strip_py_ext, import_module
from lemoncheesecake.helpers.introspection import get_object_attributes
from lemoncheesecake.exceptions import LemoncheesecakeException, UserError, ModuleImportError, \
    SuiteLoadingError, serialize_current_exception
from lemoncheesecake.suite.core import Test, Suite, SUITE_HOOKS
from lemoncheesecake.suite.builder import _get_metadata_next_rank, build_description_from_name
from lemoncheesecake.testtree import BaseTreeNode
from lemoncheesecake.helpers.typecheck import check_type_string, check_type_dict, check_type


def _is_suite_class(obj):
    return inspect.isclass(obj) and hasattr(obj, "_lccmetadata") and obj._lccmetadata.is_suite


def _is_test_method(obj):
    return inspect.ismethod(obj) and hasattr(obj, "_lccmetadata") and obj._lccmetadata.is_test


def _is_test_function(obj):
    return inspect.isfunction(obj) and hasattr(obj, "_lccmetadata") and obj._lccmetadata.is_test


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

    test = Test(md.name, md.description, obj)
    test.tags.extend(md.tags)
    test.properties.update(md.properties)
    test.links.extend(md.links)
    test.disabled = md.disabled
    test.hidden = md.condition and not md.condition(obj)
    test.rank = md.rank
    test.dependencies.extend(md.dependencies)

    try:
        _check_test_tree_node_types(test)
    except TypeError as excp:
        raise SuiteLoadingError("Invalid test metadata type for '%s': %s" % (test.name, excp))

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
        if obj._lccmetadata.parametrized:
            for test in _load_parametrized_tests(obj):
                if not test.hidden:
                    yield test
        else:
            test = _load_test(obj)
            if not test.hidden:
                yield test


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


def _get_sub_dirs_from_dir(top_dir):
    paths = [os.path.join(top_dir, path) for path in os.listdir(top_dir)]
    return sorted(filter(osp.isdir, paths))


def _normalize_link(link):
    if type(link) is str:
        return link, None
    else:
        return link


def load_suite_from_class(class_):
    # type: (Any) -> Suite
    """
    Load a suite from a class.
    """
    try:
        md = class_._lccmetadata
    except AttributeError:
        raise SuiteLoadingError("Class is not declared as a suite")

    try:
        suite_obj = class_()
    except UserError as e:
        raise e  # propagate UserError
    except Exception:
        raise LemoncheesecakeException("Got an unexpected error while instantiating suite class '%s':%s" % (
            class_.__name__, serialize_current_exception()
        ))

    suite = Suite(suite_obj, md.name, md.description)
    suite.tags.extend(md.tags)
    suite.properties.update(md.properties)
    suite.links.extend(md.links)
    suite.rank = md.rank
    suite.disabled = md.disabled
    suite.hidden = md.condition and not md.condition(suite_obj)

    try:
        _check_test_tree_node_types(suite)
    except TypeError as excp:
        raise SuiteLoadingError("Invalid suite metadata type for '%s': %s" % (suite.name, excp))

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
    return list(
        filter(
            lambda suite: not suite.hidden, map(load_suite_from_class, classes)
        )
    )


def load_suite_from_module(mod):
    # type: (Any) -> Suite
    """
    Load a suite from a module instance.
    """

    suite_info = getattr(mod, "SUITE", {})
    suite_condition = suite_info.get("visible_if")
    suite_name = suite_info.get("name", inspect.getmodulename(inspect.getfile(mod)))
    suite_description = suite_info.get("description", build_description_from_name(suite_name))

    suite = Suite(mod, suite_name, suite_description)
    suite.tags.extend(suite_info.get("tags", []))
    suite.properties.update(suite_info.get("properties", {}))
    suite.links.extend(map(_normalize_link, suite_info.get("links", [])))
    suite.rank = suite_info.get("rank", _get_metadata_next_rank())
    suite.hidden = suite_condition and not suite_condition(mod)

    try:
        _check_test_tree_node_types(suite)
    except TypeError as excp:
        raise SuiteLoadingError("Invalid suite metadata type for '%s': %s" % (suite.name, excp))

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

    Raise SuiteLoadingError if the file cannot be loaded as a suite.
    """
    try:
        mod = import_module(filename)
    except ModuleImportError as e:
        raise SuiteLoadingError(str(e))
    mod_name = strip_py_ext(osp.basename(filename))

    suite = load_suite_from_module(mod)

    # in case of module containing no tests, a single sub-suite whose name is the same a as module
    # then this sub-suite will be actually considered as the suite itself
    if not hasattr(mod, "SUITE") and \
        len(suite.get_tests()) == 0 and len(suite.get_suites()) == 1 and suite.get_suites()[0].name == mod_name:
        suite = suite.get_suites()[0]
        suite.parent_suite = None

    return suite


def load_suites_from_files(patterns, excluding=()):
    # type: (Sequence[str], Sequence[str]) -> List[Suite]

    """
    Load a list of suites from a list of files.

    :param patterns: a mandatory list (a simple string can also be used instead of a single element list)
      of files to import; the wildcard '*' character can be used
    :param excluding: an optional list (a simple string can also be used instead of a single element list)
      of elements to exclude from the expanded list of files to import

    Example::

        load_suites_from_files("test_*.py")
    """
    return list(
        filter(
            lambda suite: not suite.hidden and not suite.is_empty(),
            map(load_suite_from_file, get_matching_files(patterns, excluding))
        )
    )


def load_suites_from_directory(dir, recursive=True):
    # type: (str, bool) -> List[Suite]

    """
    Load a list of suites from a directory.

    If the recursive argument is set to True, sub suites will be searched in a directory named
    from the suite module: if the suite module is "foo.py" then the sub suites directory must be "foo".

    Raise SuiteLoadingError if one or more suite could not be loaded.
    """
    if not osp.exists(dir):
        raise SuiteLoadingError("Directory '%s' does not exist" % dir)

    suites = {}

    for filename in get_py_files_from_dir(dir):
        suite = load_suite_from_file(filename)
        if not suite.hidden:
            suites[filename] = suite

    if recursive:
        for dirname in _get_sub_dirs_from_dir(dir):
            suite = suites.get(dirname + ".py")
            if not suite:
                suite_name = osp.basename(dirname)
                suite = Suite(None, suite_name, build_description_from_name(suite_name))
                suites[suite.name] = suite
            for sub_suite in load_suites_from_directory(dirname, recursive=True):
                suite.add_suite(sub_suite)

    return sorted(sorted(filter(lambda s: not s.is_empty(), suites.values()), key=lambda s: s.name), key=lambda s: s.rank)
