from .run import RunCommand
from .bootstrap import BootstrapCommand

def get_commands():
    return [RunCommand(), BootstrapCommand()]