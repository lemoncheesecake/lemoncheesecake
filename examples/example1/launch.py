#!/usr/bin/python

import sys
sys.path.append("..")

from lemoncheesecake.launcher import Launcher
from lemoncheesecake.loader import import_testsuites_from_directory
from lemoncheesecake.worker import Worker
from lemoncheesecake.reporting import backends
from lemoncheesecake import *

class MyWorker(Worker):
    def before_all_tests(self):
        log_info("some log")
    
    def after_all_tests(self):
        log_error("some error")

launcher = Launcher()
launcher.add_reporting_backend(backends.ConsoleBackend())
launcher.add_reporting_backend(backends.JsonBackend(pretty_formatting=True))
launcher.add_reporting_backend(backends.HtmlBackend())
launcher.add_worker("myworker", MyWorker())
launcher.load_testsuites(import_testsuites_from_directory("suites"))
launcher.handle_cli()
