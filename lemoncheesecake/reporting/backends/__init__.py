from .console import ConsoleBackend
from .xml import XmlBackend
from .json_ import JsonBackend
from .html import HtmlBackend
from .junit import JunitBackend
from .reportportal import ReportPortalBackend
from .slack import SlackReportingBackend


# NB: order matters (a bit), we typically want the messages of HtmlBackend to appear
# after those from ConsoleBackend we running "lcc run"
REPORTING_BACKENDS = ConsoleBackend, XmlBackend, JsonBackend, HtmlBackend, JunitBackend, \
    ReportPortalBackend, SlackReportingBackend
