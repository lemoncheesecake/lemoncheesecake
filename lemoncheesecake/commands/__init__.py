from .run import RunCommand
from .bootstrap import BootstrapCommand
from .show import ShowCommand
from .fixtures import FixturesCommand

def get_commands():
    return [RunCommand(), BootstrapCommand(), ShowCommand(), FixturesCommand()]