#!/usr/bin/python

import sys
sys.path.append("..")

from lemoncheesecake.launcher import Launcher
from lemoncheesecake.loader import import_testsuites_from_directory
from lemoncheesecake.worker import Worker
from lemoncheesecake.reporting import get_backend, enable_backend
from lemoncheesecake import *

class MyWorker(Worker):
    def before_all_tests(self):
        log_info("some log")
    
    def after_all_tests(self):
        log_error("some error")

get_backend("json").pretty_formatting = True
# get_backend("console").display_testsuite_full_path = False

launcher = Launcher()
launcher.add_worker("myworker", MyWorker())
launcher.load_testsuites(import_testsuites_from_directory("suites"))
launcher.handle_cli()
