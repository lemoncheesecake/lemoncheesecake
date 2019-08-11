'''
Created on Jun 16, 2017

@author: nicolas
'''

import copy

from typing import Union, Tuple, List, Sequence, TypeVar

from lemoncheesecake.helpers.orderedset import OrderedSet
from lemoncheesecake.exceptions import CannotFindTreeNode


# Please note that attributes from base classes do not appear
# in generated api documentation
# (see https://github.com/sphinx-doc/sphinx/issues/741)

class BaseTreeNode(object):
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
        return len(list(self.hierarchy)) - 1

    @property
    def path(self):
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
        node = copy.copy(self)
        node.parent_suite = None
        return node

    def __str__(self):
        return self.path


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
        self._tests = []
        self._suites = []

    def add_test(self, test):
        test.parent_suite = self
        self._tests.append(test)

    def get_tests(self):
        return self._tests

    def add_suite(self, suite):
        suite.parent_suite = self
        self._suites.append(suite)

    def get_suites(self, include_empty_suites=False):
        if include_empty_suites:
            return self._suites
        else:
            return list(filter(lambda suite: not suite.is_empty(), self._suites))

    def is_empty(self):
        if len(self.get_tests()) != 0:
            return False

        for sub_suite in self.get_suites():
            if not sub_suite.is_empty():
                return False

        return True

    def pull_node(self):
        node = BaseTreeNode.pull_node(self)
        node._tests = []
        node._suites = []
        return node


S = TypeVar("S", bound=BaseSuite)


def flatten_suites(suites):
    for suite in suites:
        yield suite
        for sub_suite in flatten_suites(suite.get_suites()):
            yield sub_suite


def flatten_tests(suites):
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
            raise CannotFindTreeNode("Cannot find suite named '%s' within %s" % (
                lookup_suite_name, [s.name for s in lookup_suites]
            ))

        lookup_suites = lookup_suite.get_suites(include_empty_suites=True)

    return lookup_suite


def find_test(suites, hierarchy):
    # type: (Sequence[BaseSuite], TreeNodeHierarchy) -> T

    hierarchy = normalize_node_hierarchy(hierarchy)

    suite = find_suite(suites, hierarchy[:-1])

    try:
        return next(t for t in suite.get_tests() if t.name == hierarchy[-1])
    except StopIteration:
        raise CannotFindTreeNode("Cannot find test named '%s'" % hierarchy[-1])
