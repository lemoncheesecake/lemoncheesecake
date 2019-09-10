#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lemoncheesecake.cli import main

sys.exit(main())
