'''
Created on Jun 16, 2017

@author: nicolas
'''

from lemoncheesecake.utils import get_distincts_in_list
from lemoncheesecake.exceptions import CannotFindTreeNode


class BaseTreeNode:
    def __init__(self, name, description):
        self.parent_suite = None
        self.name = name
        self.description = description
        self.tags = [ ]
        self.properties = {}
        self.links = [ ]

    def get_path(self):
        path = [ self ]
        parent_suite = self.parent_suite
        while parent_suite != None:
            path.insert(0, parent_suite)
            parent_suite = parent_suite.parent_suite
        return path
    
    def get_path_as_str(self, sep="."):
        return sep.join([s.name for s in self.get_path()])

    def get_depth(self):
        return len(self.get_path()) - 1

    def get_inherited_paths(self):
        return list(map(lambda node: node.get_path_as_str(), self.get_path()))

    def get_inherited_descriptions(self):
        return list(map(lambda node: node.description, self.get_path()))

    def get_inherited_tags(self):
        tags = []
        for node in self.get_path():
            tags.extend(node.tags)
        return get_distincts_in_list(tags)

    def get_inherited_properties(self):
        properties = {}
        for node in self.get_path():
            properties.update(node.properties)
        return properties

    def get_inherited_links(self):
        links = []
        for node in self.get_path():
            links.extend(node.links)
        return get_distincts_in_list(links)

    def __str__(self):
        return self.get_path_as_str()


class BaseTest(BaseTreeNode):
    pass


class BaseSuite(BaseTreeNode):
    def __init__(self, name, description):
        BaseTreeNode.__init__(self, name, description)
        self._tests = []
        self._suites = []
        self._selected_test_names = []

    def add_test(self, test):
        test.parent_suite = self
        self._tests.append(test)
        self._selected_test_names.append(test.name)

    def get_tests(self, skip_filter=False):
        if skip_filter:
            return self._tests
        else:
            return list(filter(self.is_test_selected, self._tests))
    
    def add_suite(self, suite):
        suite.parent_suite = self
        self._suites.append(suite)

    def get_suites(self, allow_empty_suite=False):
        if allow_empty_suite:
            return self._suites
        else:
            return list(filter(lambda suite: suite.has_selected_tests(deep=True), self._suites))

    def apply_filter(self, filter):
        self._selected_test_names = [ ]

        for test in self._tests:
            if filter.match_test(test, self):
                self._selected_test_names.append(test.name)

        for suite in self._suites:
            suite.apply_filter(filter)

    def has_selected_tests(self, deep=True):
        if deep:
            if self._selected_test_names:
                return True

            for suite in self.get_suites():
                if suite.has_selected_tests():
                    return True

            return False
        else:
            return bool(self._selected_test_names)

    def is_test_selected(self, test):
        return test.name in self._selected_test_names


def walk_suites(suites, suite_func=None, test_func=None):
    def do_walk(suite):
        if suite_func:
            suite_func(suite)
        if test_func:
            for test in suite.get_tests():
                test_func(test, suite)
        for sub_suite in suite.get_suites():
            do_walk(sub_suite)
    for suite in suites:
        do_walk(suite)


def walk_tests(suites, func):
    walk_suites(suites, test_func=func)


def get_flattened_suites(suites):
    flattened_suites = []
    walk_suites(suites, lambda suite: flattened_suites.append(suite))
    return flattened_suites


def get_suite_by_name(suites, suite_name):
    try:
        return next(s for s in suites if s.name == suite_name)
    except StopIteration:
        raise CannotFindTreeNode("Cannot find suite named '%s'" % suite_name)


def find_suite(suites, path, sep="."):
    lookup_suites = suites
    lookup_suite = None
    for lookup_suite_name in path.split(sep):
        lookup_suite = get_suite_by_name(lookup_suites, lookup_suite_name)
        lookup_suites = lookup_suite.get_suites(allow_empty_suite=True)
    if lookup_suite is None:
        raise CannotFindTreeNode("Cannot find suite named '%s'" % path)

    return lookup_suite


def get_test_by_name(suite, test_name):
    try:
        return next(t for t in suite.get_tests(skip_filter=True) if t.name == test_name)
    except StopIteration:
        raise CannotFindTreeNode("Cannot find test named '%s'" % test_name)


def find_test(suites, path, sep="."):
    suite_name = sep.join(path.split(sep)[:-1])
    lookup_suite = find_suite(suites, suite_name, sep=sep)
    return get_test_by_name(lookup_suite, path.split(sep)[-1])