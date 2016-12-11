#!/usr/bin/python

import sys
sys.path.append("..")

from lemoncheesecake.launcher import Launcher
from lemoncheesecake.loader import import_testsuites_from_directory
from lemoncheesecake.workers import Worker, add_worker
from lemoncheesecake.reporting import get_backend, enable_backend
from lemoncheesecake import *

class MyWorker(Worker):
    def before_all_tests(self):
        log_info("some log")
    
    def after_all_tests(self):
        log_error("some error")

add_worker("myworker", MyWorker())

get_backend("json").pretty_formatting = True
# get_backend("console").display_testsuite_full_path = False

launcher = Launcher()
launcher.load_testsuites(import_testsuites_from_directory("suites"))
launcher.handle_cli()
