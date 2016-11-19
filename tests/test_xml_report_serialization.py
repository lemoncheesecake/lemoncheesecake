'''
Created on Nov 17, 2016

@author: nicolas
'''

import pytest

from lemoncheesecake.reporting.backends import XmlBackend

from report_serialization_tests import *

@pytest.fixture
def backend():
    return XmlBackend()