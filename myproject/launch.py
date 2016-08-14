#!/usr/bin/python

import sys
sys.path.append("..")

from lemoncheesecake.launcher import Launcher, get_testsuites_from_directory
from lemoncheesecake.testsuite import MetadataValidator
from lemoncheesecake.worker import Worker
from lemoncheesecake.reporting import get_backend, enable_backend

class MyWorker(Worker):
    pass

enable_backend("xml")
get_backend("json").pretty_formatting = True
#get_backend("xml").indent_level = 2

# metadata_validator = MetadataValidator()
# metadata_validator.set_test_metadata_accepted_values("priority", ("low", "medium", "high"))
# metadata_validator.make_suite_metadata_mandatory("type")

launcher = Launcher()
launcher.set_worker(MyWorker())
launcher.load_testsuites(get_testsuites_from_directory("suites"))
launcher.handle_cli()
