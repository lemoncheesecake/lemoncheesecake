'''
Created on Sep 8, 2016

@author: nicolas
'''

import fnmatch

__all__ = ("Filter", "add_filter_args_to_cli_parser", "get_filter_from_cli_args")

NEGATIVE_FILTER_CHARS = "-^~"

def match_values(values, patterns):
    if not patterns:
        return True
    
    for pattern in patterns:
        if pattern[0] in NEGATIVE_FILTER_CHARS:
            if not fnmatch.filter(values, pattern[1:]):
                return True
        else:
            if fnmatch.filter(values, pattern):
                return True
    return False

def match_keyvalues(keyvalues, patterns):
    if not patterns:
        return True
    
    for key, value in patterns.items():
        if key in keyvalues:
            if value[0] in NEGATIVE_FILTER_CHARS:
                if keyvalues[key] != value[1:]:
                    return True
            else:
                if keyvalues[key] == value:
                    return True
    return False

def match_listelem(lsts, idx, patterns):
    if not patterns:
        return True
    
    for pattern in patterns:
        if pattern[0] in NEGATIVE_FILTER_CHARS:
            if pattern[1:] not in map(lambda l: l[idx], lsts):
                return True
        else:
            if pattern in map(lambda l: l[idx], lsts):
                return True
    return False

class Filter:
    def __init__(self):
        self.path = []
        self.description = []
        self.tags = [ ]
        self.properties = {}
        self.link_names = [ ]
    
    def is_empty(self):
        return not any([self.path, self.description, self.tags, self.properties, self.link_names])
    
    def match_test(self, test, suite):
        funcs = [
            lambda: match_values(test.get_inherited_paths(), self.path),
            lambda: match_values(test.get_inherited_descriptions(), self.description),
            lambda: match_values(test.get_inherited_tags(), self.tags),
            lambda: match_keyvalues(test.get_inherited_properties(), self.properties),
            lambda: match_listelem(test.get_inherited_links(), 1, self.link_names)
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