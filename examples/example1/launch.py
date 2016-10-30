#!/usr/bin/python

import sys
sys.path.append("..")

from lemoncheesecake.launcher import Launcher, import_testsuites_from_directory
from lemoncheesecake.worker import Worker
from lemoncheesecake.reporting import get_backend, enable_backend

class MyWorker(Worker):
    pass

enable_backend("xml")
get_backend("json").pretty_formatting = True
get_backend("xml").indent_level = 4

launcher = Launcher()
launcher.set_worker(MyWorker())
launcher.load_testsuites(import_testsuites_from_directory("suites"))
launcher.handle_cli()
