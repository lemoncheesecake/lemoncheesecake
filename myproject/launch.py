#!/usr/bin/python

import sys
sys.path.append("..")

from lemoncheesecake.launcher import Launcher, load_testsuites_from_directory

launcher = Launcher()
launcher.add_testsuites(load_testsuites_from_directory("suites"))
launcher.handle_cli()
