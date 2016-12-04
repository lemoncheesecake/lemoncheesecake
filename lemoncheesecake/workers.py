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

def clear_workers():
    global _workers
    _workers.clear()

def get_workers_with_hook_before_all_tests():
    return list(filter(lambda b: b.has_hook("before_all_tests"), get_workers()))

def get_workers_with_hook_after_all_tests():
    return list(filter(lambda b: b.has_hook("after_all_tests"), get_workers()))