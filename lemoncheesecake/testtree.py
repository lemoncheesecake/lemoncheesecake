'''
Created on Jun 16, 2017

@author: nicolas
'''

import copy
from collections import OrderedDict

from typing import Union, Tuple, List, Sequence, TypeVar, Generator

from lemoncheesecake.helpers.orderedset import OrderedSet


# Please note that attributes from base classes do not appear
# in generated api documentation
# (see https://github.com/sphinx-doc/sphinx/issues/741)

class BaseTreeNode(object):
    """
    :var name: name
    """

    def __init__(self, name, description):
        self.parent_suite = None
        #: name
        self.name = name
        #: description
        self.description = description
        #: tags, as a list
        self.tags = []
        #: properties, as a dict
        self.properties = {}
        #: links, as a list
        self.links = []

    @property
    def hierarchy(self):
        if self.parent_suite is not None:
            for node in self.parent_suite.hierarchy:
                yield node
        yield self

    @property
    def hierarchy_depth(self):
        # type: () -> int
        return len(list(self.hierarchy)) - 1

    @property
    def path(self):
        # type: () -> str
        """
        The complete path of the test node (example: if used on a test named "my_test" and a suite named
        "my_suite", then the path is "my_suite.my_test").
        """
        return ".".join(node.name for node in self.hierarchy)

    @property
    def hierarchy_paths(self):
        return (node.path for node in self.hierarchy)

    @property
    def hierarchy_descriptions(self):
        return (node.description for node in self.hierarchy)

    @property
    def hierarchy_tags(self):
        tags = OrderedSet()
        for node in self.hierarchy:
            tags.update(node.tags)
        return tags

    @property
    def hierarchy_properties(self):
        properties = {}
        for node in self.hierarchy:
            properties.update(node.properties)
        return properties

    @property
    def hierarchy_links(self):
        links = OrderedSet()
        for node in self.hierarchy:
            links.update(node.links)
        return links

    def pull_node(self):
        # type: () -> "_N"
        node = copy.copy(self)
        node.parent_suite = None
        return node

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, self.path)


_N = TypeVar("_N", bound=BaseTreeNode)


TreeNodeHierarchy = Union[Tuple[str, ...], List, BaseTreeNode, str]


def normalize_node_hierarchy(hierarchy):
    # type: (TreeNodeHierarchy) -> Tuple[str, ...]
    if type(hierarchy) is tuple:
        return hierarchy
    elif type(hierarchy) is list:
        return tuple(hierarchy)
    elif isinstance(hierarchy, BaseTreeNode):
        return tuple(p.name for p in hierarchy.hierarchy)
    else:  # assume str
        return tuple(hierarchy.split("."))


class BaseTest(BaseTreeNode):
    pass


T = TypeVar("T", bound=BaseTest)


class BaseSuite(BaseTreeNode):
    def __init__(self, name, description):
        BaseTreeNode.__init__(self, name, description)
        # NB: use OrderedDict instead of list to enable fast test lookup in suites
        # containing a large number of tests
        self._tests = OrderedDict()
        self._suites = []

    def add_test(self, test):
        """
        Add test to the suite.
        """
        test.parent_suite = self
        self._tests[test.name] = test

    def get_tests(self):
        """
        Get suite's tests.
        """
        return list(self._tests.values())

    def get_test_by_name(self, name):
        return self._tests[name]

    def add_suite(self, suite):
        """
        Add a sub-suite to the suite.
        """
        suite.parent_suite = self
        self._suites.append(suite)

    def get_suites(self):
        return self._suites

    def is_empty(self):
        if len(self.get_tests()) != 0:
            return False

        for sub_suite in self.get_suites():
            if not sub_suite.is_empty():
                return False

        return True

    def pull_node(self):
        # type: () -> "BaseSuite"
        node = BaseTreeNode.pull_node(self)
        node._tests = OrderedDict()
        node._suites = []
        return node

    def filter(self, test_filter):
        suite = self.pull_node()

        for test in self.get_tests():
            if test_filter(test):
                suite.add_test(test.pull_node())

        for sub_suite in filter_suites(self.get_suites(), test_filter):
            suite.add_suite(sub_suite)

        return suite


def filter_suites(suites, test_filter):
    return list(
        filter(
            lambda s: not s.is_empty(), (s.filter(test_filter) for s in suites)
        )
    )


S = TypeVar("S", bound=BaseSuite)


def flatten_suites(suites):
    # type: (Sequence[S]) -> Generator[S]
    for suite in suites:
        yield suite
        for sub_suite in flatten_suites(suite.get_suites()):
            yield sub_suite


def flatten_tests(suites):
    # type: (Sequence[S]) -> Generator[T]
    for suite in flatten_suites(suites):
        for test in suite.get_tests():
            yield test


def find_suite(suites, hierarchy):
    # type: (Sequence[S], TreeNodeHierarchy) -> S

    hierarchy = normalize_node_hierarchy(hierarchy)

    lookup_suites = suites
    lookup_suite = None
    for lookup_suite_name in hierarchy:
        try:
            lookup_suite = next(s for s in lookup_suites if s.name == lookup_suite_name)
        except StopIteration:
            raise LookupError("Cannot find suite named '%s' within %s" % (
                lookup_suite_name, [s.name for s in lookup_suites]
            ))

        lookup_suites = lookup_suite.get_suites()

    return lookup_suite


def find_test(suites, hierarchy):
    # type: (Sequence[BaseSuite], TreeNodeHierarchy) -> T

    hierarchy = normalize_node_hierarchy(hierarchy)

    suite = find_suite(suites, hierarchy[:-1])
    try:
        return suite.get_test_by_name(hierarchy[-1])
    except KeyError:
        raise LookupError("Cannot find test named '%s'" % ".".join(hierarchy))
