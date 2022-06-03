from .run import RunCommand
from .bootstrap import BootstrapCommand
from .show import ShowCommand
from .fixtures import FixturesCommand
from .stats import StatsCommand
from .report import ReportCommand
from .diff import DiffCommand
from .version import VersionCommand
from .top import TopTests, TopSuites, TopSteps
from .check import CheckCommand


def get_commands():
    return [
        RunCommand(), CheckCommand(), BootstrapCommand(),
        ShowCommand(), FixturesCommand(), StatsCommand(),
        ReportCommand(), DiffCommand(),
        TopTests(), TopSuites(), TopSteps(),
        VersionCommand()
    ]
