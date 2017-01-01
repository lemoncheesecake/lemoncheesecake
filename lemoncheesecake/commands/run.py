'''
Created on Dec 31, 2016

@author: nicolas
'''

from lemoncheesecake.loader import load_testsuites_from_project
from lemoncheesecake.project import Project
from lemoncheesecake.launcher import Launcher
from lemoncheesecake import reporting

def run():
    project = Project()
    launcher = Launcher(project.get_project_dir())
    launcher.set_report_dir_creation_callback(project.get_report_dir_creation_cb())
    
    for worker_name, worker in project.get_workers().items():
        launcher.add_worker(worker_name, worker)
    for backend in project.get_reporting_backends(capabilities=reporting.CAPABILITY_REPORTING_SESSION, active_only=False):
        launcher.add_reporting_backend(backend, is_active=project.is_reporting_backend_active(backend.name))
    launcher.set_testsuites(load_testsuites_from_project(project))
    
    project.add_cli_extra_args(launcher.get_cli_args_parser())
    launcher.handle_cli()

if __name__ == "__main__":
    run()