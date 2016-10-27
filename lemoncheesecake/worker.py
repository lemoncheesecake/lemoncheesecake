'''
Created on Mar 18, 2016

@author: nicolas
'''

class Worker:
    def cli_initialize(self, cli_args):
        """
        Hook method for initializing the worker from CLI arguments (cli_args is the result of the
        parse_args method of a ArgumentParser instance of argparse).
        The
        """
        pass
    
    def before_tests(self):
        """Hook method called before the beginning of tests execution"""
        pass
    
    def after_tests(self):
        """Hook method called after the end of tests execution"""
        pass
