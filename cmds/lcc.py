#!/usr/bin/env python

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from lemoncheesecake.cli import main

sys.exit(main())