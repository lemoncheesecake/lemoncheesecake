#!/usr/bin/python

import sys
import os.path

script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.append(script_dir)

from lemoncheesecake.launcher import Launcher

launcher = Launcher()
launcher.handle_cli()