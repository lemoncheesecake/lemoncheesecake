from .run import RunCommand
from .bootstrap import BootstrapCommand
from .show import ShowCommand
from .fixtures import FixturesCommand
from .stats import StatsCommand

def get_commands():
    return [RunCommand(), BootstrapCommand(), ShowCommand(), FixturesCommand(), StatsCommand()]