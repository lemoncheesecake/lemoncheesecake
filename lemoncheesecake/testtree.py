'''
Created on Jun 16, 2017

@author: nicolas
'''

from lemoncheesecake.utils import get_distincts_in_list

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
    
    def add_test(self, test):
        test.parent_suite = self
        self._tests.append(test)
    
    def get_tests(self):
        return self._tests
    
    def add_suite(self, suite):
        suite.parent_suite = self
        self._suites.append(suite)

    def get_suites(self):
        return self._suites
    
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
