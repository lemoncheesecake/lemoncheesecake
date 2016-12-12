'''
Created on Mar 18, 2016

@author: nicolas
'''

from lemoncheesecake.exceptions import ProgrammingError
from lemoncheesecake.utils import object_has_method

class Worker:
    def cli_initialize(self, cli_args):
        """
        Hook method for initializing the worker from CLI arguments (cli_args is the result of the
        parse_args method of a ArgumentParser instance of argparse).
        The
        """
        pass
    
    def has_hook(self, hook_name):
        return object_has_method(self, hook_name)

#     def before_all_tests(self):
#         """Hook method called before the beginning of tests execution"""
#         pass
    
#     def after_all_tests(self):
#         """Hook method called after the end of tests execution"""
#         pass
