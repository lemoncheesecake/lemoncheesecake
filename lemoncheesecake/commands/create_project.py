'''
Created on Jan 4, 2017

@author: nicolas
'''

import os
import argparse

from lemoncheesecake import project

def create_project():
    cli_parser = argparse.ArgumentParser("Create lemoncheesecake project")
    cli_parser.add_argument("dir", help="The directory where the project must be created")
    cli_args = cli_parser.parse_args()

    try:
        os.mkdir(cli_args.dir)
    except (IOError, OSError) as e:
        return "Cannot create project directory '%s': %s" % (cli_args.dir, e)
        
    try:
        project.create_project(cli_args.dir)
    except (IOError, OSError) as e:
        return "Cannot create project '%s': %s" % (cli_args.dir, e)