'''
Created on Nov 19, 2016

@author: nicolas
'''

import pytest

from lemoncheesecake.reporting.backends import JsonBackend

from report_serialization_tests import *

@pytest.fixture
def backend():
    return JsonBackend()