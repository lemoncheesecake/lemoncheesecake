#!/usr/bin/python

import sys
sys.path.append("..")

from lemoncheesecake.launcher import Launcher, get_testsuites_from_directory

launcher = Launcher()
launcher.load_testsuites(get_testsuites_from_directory("suites"))
launcher.handle_cli()
