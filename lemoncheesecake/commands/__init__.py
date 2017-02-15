from .run import RunCommand
from .bootstrap import BootstrapCommand
from .show import ShowCommand

def get_commands():
    return [RunCommand(), BootstrapCommand(), ShowCommand()]