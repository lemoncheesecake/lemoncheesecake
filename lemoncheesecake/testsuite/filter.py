'''
Created on Sep 8, 2016

@author: nicolas
'''

import fnmatch

FILTER_SUITE_MATCH_ID = 0x01
FILTER_SUITE_MATCH_DESCRIPTION = 0x02
FILTER_SUITE_MATCH_TAG = 0x04
FILTER_SUITE_MATCH_URL_NAME = 0x08
FILTER_SUITE_MATCH_PROPERTY = 0x10

__all__ = ("Filter",)

class Filter:
    def __init__(self):
        self.test_id = []
        self.test_description = []
        self.testsuite_id = []
        self.testsuite_description = []
        self.tags = [ ]
        self.properties = {}
        self.url_names = [ ]
    
    def is_empty(self):
        count = 0
        for value in self.test_id, self.testsuite_id, self.test_description, \
            self.testsuite_description, self.tags, self.properties, self.url_names:
            count += len(value)
        return count == 0
    
    def get_flags_to_match_testsuite(self):
        flags = 0
        if self.testsuite_id:
            flags |= FILTER_SUITE_MATCH_ID
        if self.testsuite_description:
            flags |= FILTER_SUITE_MATCH_DESCRIPTION
        return flags
    
    def match_test(self, test, parent_suite_match=0):
        match = False
        
        if self.test_id:
            for id in self.test_id:
                if fnmatch.fnmatch(test.id, id):
                    match = True
                    break
            if not match:
                return False
        
        if self.test_description:
            for desc in self.test_description:
                if fnmatch.fnmatch(test.description, desc):
                    match = True
                    break
            if not match:
                return False
        
        if self.tags and not parent_suite_match & FILTER_SUITE_MATCH_TAG:
            for tag in self.tags:
                if fnmatch.filter(test.tags, tag):
                    match = True
                    break
            if not match:
                return False
                
        if self.properties and not parent_suite_match & FILTER_SUITE_MATCH_PROPERTY:
            for key, value in self.properties.items():
                if key in test.properties and test.properties[key] == value:
                    match = True
                    break
            if not match:
                return False
                
        if self.url_names and not parent_suite_match & FILTER_SUITE_MATCH_URL_NAME:
            for url in self.url_names:
                if url in [ u[1] for u in test.urls if u[1] ]:
                    match = True
                    break
            if not match:
                return False
        
        return True
    
    def match_testsuite(self, suite, parent_suite_match=0):
        match = 0
        
        if self.testsuite_id and not parent_suite_match & FILTER_SUITE_MATCH_ID:
            for id in self.testsuite_id:
                if fnmatch.fnmatch(suite.id, id):
                    match |= FILTER_SUITE_MATCH_ID
                    break
                
        if self.testsuite_description and not parent_suite_match & FILTER_SUITE_MATCH_DESCRIPTION:
            for desc in self.testsuite_description:
                if fnmatch.fnmatch(suite.description, desc):
                    match |= FILTER_SUITE_MATCH_DESCRIPTION
                    break

        if self.tags and not parent_suite_match & FILTER_SUITE_MATCH_TAG:
            for tag in self.tags:
                if fnmatch.filter(suite.tags, tag):
                    match |= FILTER_SUITE_MATCH_TAG
                    break

        if self.properties and not parent_suite_match & FILTER_SUITE_MATCH_PROPERTY:
            for key, value in self.properties.items():
                if key in suite.properties and suite.properties[key] == value:
                    match |= FILTER_SUITE_MATCH_PROPERTY
                    break

        if self.url_names and not parent_suite_match & FILTER_SUITE_MATCH_URL_NAME:
            for url in self.url_names:
                if url in [ u[0] for u in suite.urls ]:
                    match |= FILTER_SUITE_MATCH_URL_NAME
                    break

        return match