from .run import RunCommand
from .bootstrap import BootstrapCommand
from .show import ShowCommand
from .fixtures import FixturesCommand
from .stats import StatsCommand
from .report import ReportCommand
from .version import VersionCommand


def get_commands():
    return [
        RunCommand(), BootstrapCommand(),
        ShowCommand(), FixturesCommand(), StatsCommand(),
        ReportCommand(),
        VersionCommand()
    ]
