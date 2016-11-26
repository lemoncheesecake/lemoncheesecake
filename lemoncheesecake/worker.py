'''
Created on Mar 18, 2016

@author: nicolas
'''

from lemoncheesecake.exceptions import ProgrammingError

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

_workers = {}

def add_worker(worker_name, worker):
    global _workers
    _workers[worker_name] = worker

def get_worker_names():
    return _workers.keys()

def get_worker(worker_name):
    return _workers[worker_name]

def get_workers():
    return _workers.values()