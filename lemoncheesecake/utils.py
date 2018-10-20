'''
Created on Mar 18, 2016

@author: nicolas
'''

import os
import sys
import re

IS_PYTHON3 = sys.version_info > (3,)
IS_PYTHON2 = sys.version_info < (3,)


def get_resource_path(relpath):
    return os.path.join(os.path.dirname(__file__), "resources", relpath)


# borrowed from https://stackoverflow.com/a/1176023
def camel_case_to_snake_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
