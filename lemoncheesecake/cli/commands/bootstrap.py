'''
Created on Jan 4, 2017

@author: nicolas
'''

import os

from lemoncheesecake.cli.command import Command
from lemoncheesecake.project import create_project

class BootstrapCommand(Command):
    def get_name(self):
        return "bootstrap"
    
    def get_description(self):
        return "Create a new lemoncheesecake project"
    
    def add_cli_args(self, cli_parser):
        cli_parser.add_argument("dir", help="The directory where the project must be created")

    def run_cmd(self, cli_args):
        try:
            os.mkdir(cli_args.dir)
        except (IOError, OSError) as e:
            return "Cannot create project directory '%s': %s" % (cli_args.dir, e)
            
        try:
            create_project(cli_args.dir)
        except (IOError, OSError) as e:
            return "Cannot create project '%s': %s" % (cli_args.dir, e)
        
        return 0