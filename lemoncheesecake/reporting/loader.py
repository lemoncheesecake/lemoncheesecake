import os
import os.path as osp
from typing import Sequence, Iterator

from lemoncheesecake.exceptions import ReportLoadingError
from lemoncheesecake.reporting.report import Report
from lemoncheesecake.reporting.backend import get_reporting_backends, ReportUnserializerMixin, ReportingBackend


def load_report_from_file(filename, backends=None):
    # type: (str, Sequence[ReportingBackend]) -> Report
    if backends is None:
        backends = get_reporting_backends()
    for backend in backends:
        if isinstance(backend, ReportUnserializerMixin):
            try:
                return backend.load_report(filename)
            except IOError as excp:
                raise ReportLoadingError("Cannot load report from file '%s': %s" % (filename, excp))
            except ReportLoadingError:
                pass
    raise ReportLoadingError("Cannot find any suitable report backend to load report file '%s'" % filename)


def load_reports_from_dir(dirname, backends=None):
    # type: (str, Sequence[ReportingBackend]) -> Iterator[Report]
    for filename in [os.path.join(dirname, filename) for filename in os.listdir(dirname)]:
        if os.path.isfile(filename):
            try:
                yield load_report_from_file(filename, backends)
            except ReportLoadingError:
                pass


def load_report(path, backends=None):
    # type: (str, Sequence[ReportingBackend]) -> Report
    """
    Load report from a report directory or file.
    """
    if osp.isdir(path):
        try:
            return next(load_reports_from_dir(path, backends))
        except StopIteration:
            raise ReportLoadingError("Cannot find any report in directory '%s'" % path)
    else:
        return load_report_from_file(path, backends)
