#!/usr/bin/python

import sys
sys.path.append("..")

from lemoncheesecake.launcher import Launcher, get_testsuites_from_directory
from lemoncheesecake.worker import Worker

class MyWorker(Worker):
    pass

launcher = Launcher()
launcher.set_worker(MyWorker())
launcher.load_testsuites(get_testsuites_from_directory("suites"))
launcher.handle_cli()
