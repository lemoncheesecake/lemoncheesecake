'''
Created on Sep 8, 2016

@author: nicolas
'''

import fnmatch

__all__ = ("Filter", "add_filter_args_to_cli_parser", "get_filter_from_cli_args")

def _get_path(suite, test=None):
    return ".".join([s.name for s in suite.get_path()] + ([test.name] if test else []))

def match_values(values, patterns):
    if not patterns:
        return 1
    
    for pattern in patterns:
        if fnmatch.filter(values, pattern):
            return 1
    return 0

def match_keyvalues(keyvalues, patterns):
    if not patterns:
        return 1
    
    for key, value in patterns.items():
        if key in keyvalues and keyvalues[key] == value:
            return 1
    return 0

def match_listelem(lsts, idx, patterns):
    if not patterns:
        return 1
    
    for pattern in patterns:
        if pattern in map(lambda l: l[idx], lsts):
            return 1
    return 0

class Filter:
    def __init__(self):
        self.path = []
        self.description = []
        self.tags = [ ]
        self.properties = {}
        self.link_names = [ ]
    
    def is_empty(self):
        count = 0
        for value in self.path, self.test_description, \
            self.testsuite_description, self.tags, self.properties, self.link_names:
            count += len(value)
        return count == 0
    
    def match_test(self, test, suite):
        funcs = [
            lambda: match_values(suite.get_inherited_test_paths(test), self.path),
            lambda: match_values(suite.get_inherited_test_descriptions(test), self.description),
            lambda: match_values(suite.get_inherited_test_tags(test), self.tags),
            lambda: match_keyvalues(suite.get_inherited_test_properties(test), self.properties),
            lambda: match_listelem(suite.get_inherited_test_links(test), 1, self.link_names)
        ]
        return all(func() for func in funcs)

def add_filter_args_to_cli_parser(cli_parser):
    def property_value(value):
        splitted = value.split(":")
        if len(splitted) != 2:
            raise ValueError()
        return splitted

    cli_parser.add_argument("path", nargs="*", default=[], help="Filters on test/testsuite path (wildcard character '*' can be used)")
    cli_parser.add_argument("--desc", nargs="+", default=[], help="Filters on test/testsuite descriptions")
    cli_parser.add_argument("--tag", "-a", nargs="+", default=[], help="Filters on test & test suite tags")
    cli_parser.add_argument("--property", "-m", nargs="+", type=property_value, default=[], help="Filters on test & test suite property")
    cli_parser.add_argument("--link", "-l", nargs="+", default=[], help="Filters on test & test suite link names")

def get_filter_from_cli_args(cli_args):
    filter = Filter()
    filter.path = cli_args.path
    filter.description = cli_args.desc
    filter.tags = cli_args.tag
    filter.properties = dict(cli_args.property)
    filter.link_names = cli_args.link
    return filter