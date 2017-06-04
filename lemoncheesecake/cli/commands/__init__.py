from .run import RunCommand
from .bootstrap import BootstrapCommand
from .tree import TreeCommand
from .fixtures import FixturesCommand
from .stats import StatsCommand

def get_commands():
    return [RunCommand(), BootstrapCommand(), TreeCommand(), FixturesCommand(), StatsCommand()]