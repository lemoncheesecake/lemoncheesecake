#!/usr/bin/env python

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from lemoncheesecake.commands.create_project import create_project

sys.exit(create_project())