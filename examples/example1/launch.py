#!/usr/bin/python

import sys
sys.path.append("..")

from lemoncheesecake.launcher import Launcher, import_testsuites_from_directory
from lemoncheesecake.worker import Worker, add_worker
from lemoncheesecake.reporting import get_backend, enable_backend

class MyWorker(Worker):
    pass
add_worker("myworker", MyWorker())

enable_backend("xml")
get_backend("json").pretty_formatting = True
get_backend("xml").indent_level = 4

launcher = Launcher()
launcher.load_testsuites(import_testsuites_from_directory("suites"))
launcher.handle_cli()
