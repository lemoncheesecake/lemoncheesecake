from .console import ConsoleBackend
from .xml import XmlBackend
from .json_ import JsonBackend
from .html import HtmlBackend
from .junit import JunitBackend
from .reportportal import ReportPortalBackend
from .slack import SlackReportingBackend


REPORTING_BACKENDS = ConsoleBackend, XmlBackend, JsonBackend, HtmlBackend, JunitBackend, \
    ReportPortalBackend, SlackReportingBackend
