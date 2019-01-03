from __future__ import print_function

import os
import os.path as osp
import sys
import tempfile
import shutil

from lemoncheesecake.suite.loader import load_suites_from_classes, load_suite_from_file
from lemoncheesecake import runner
from lemoncheesecake.runtime import get_runtime
from lemoncheesecake.reporting.backends.xml import serialize_report_as_string
from lemoncheesecake.fixtures import FixtureRegistry, load_fixtures_from_func
from lemoncheesecake.project import create_project
from lemoncheesecake import events
from lemoncheesecake.cli import main
from lemoncheesecake.suite import load_suite_from_class
import lemoncheesecake.api as lcc


def build_test_module(name="mysuite"):
    return """
import lemoncheesecake.api as lcc

@lcc.suite("Test Suite")
class {name}:
    @lcc.test("This is a test")
    def test_{name}(self):
        pass
""".format(name=name)


def build_fixture_module(name="myfixture"):
    return """
import lemoncheesecake.api as lcc

@lcc.fixture()
def {name}():
    pass
""".format(name=name)


def build_test_project(params={}, extra_imports=[], static_content=""):
    return """
from lemoncheesecake.reporting import backends
from lemoncheesecake.fixtures import load_fixtures_from_file, load_fixtures_from_files, load_fixtures_from_directory
from lemoncheesecake.suite.loader import *

from lemoncheesecake import validators

{EXTRA_IMPORTS}

{STATIC_CONTENT}

{PARAMS}
""".format(
    PARAMS="\n".join(["%s = %s" % (p, v) for p, v in params.items()]),
    EXTRA_IMPORTS="\n".join(extra_imports),
    STATIC_CONTENT=static_content
)


def _remove_py_file(filename):
    os.unlink(filename)
    if osp.exists(filename + "c"):
        os.unlink(filename + "c")
    if osp.exists(filename + "o"):
        os.unlink(filename + "o")


def build_suite_from_module(module_content):
    fd, filename = tempfile.mkstemp(suffix=".py")
    fh = open(filename, "w")
    fh.write("import lemoncheesecake.api as lcc\n")
    fh.write("from lemoncheesecake.matching import *\n")
    fh.write("SUITE = {'description': 'My Suite'}\n\n")
    fh.write(module_content)
    fh.close()
    os.close(fd)
    suite = load_suite_from_file(filename)
    _remove_py_file(filename)

    return suite


def generate_project(project_dir, module_name, module_content, fixtures_content=None):
    create_project(project_dir)
    with open(osp.join(project_dir, "suites", "%s.py" % module_name), "w") as fh:
        fh.write(module_content)
    if fixtures_content:
        with open(osp.join(project_dir, "fixtures", "fixtures.py"), "w") as fh:
            fh.write(fixtures_content)


def build_fixture_registry(*funcs):
    registry = FixtureRegistry()
    for func in funcs:
        registry.add_fixtures(load_fixtures_from_func(func))
    return registry


def run_suites(suites, fixtures=None, backends=None, tmpdir=None, force_disabled=False, stop_on_failure=False,
               report_saving_strategy=None):
    if fixtures is None:
        fixture_registry = FixtureRegistry()
    else:
        if isinstance(fixtures, FixtureRegistry):
            fixture_registry = fixtures
        else:
            fixture_registry = build_fixture_registry(*fixtures)

    if backends is None:
        backends = []

    events.reset()

    if tmpdir:
        runner.run_suites(
            suites, fixture_registry, backends, tmpdir.strpath,
            force_disabled=force_disabled, stop_on_failure=stop_on_failure
        )
    else:
        report_dir = tempfile.mkdtemp()
        try:
            runner.run_suites(
                suites, fixture_registry, backends, report_dir,
                force_disabled=force_disabled, stop_on_failure=stop_on_failure,
                report_saving_strategy=report_saving_strategy
            )
        finally:
            shutil.rmtree(report_dir)

    report = get_runtime().report
    dump_report(report)

    return report


def run_suite_classes(suite_classes, fixtures=None, backends=None, tmpdir=None,
                      force_disabled=False, stop_on_failure=False, report_saving_strategy=None):
    suites = load_suites_from_classes(suite_classes)
    return run_suites(
        suites, fixtures=fixtures, backends=backends, tmpdir=tmpdir,
        force_disabled=force_disabled, stop_on_failure=stop_on_failure,
        report_saving_strategy=report_saving_strategy
    )


def run_suite(suite, fixtures=None, backends=[], tmpdir=None, force_disabled=False, stop_on_failure=False,
              report_saving_strategy=None):
    return run_suites(
        [suite], fixtures=fixtures, backends=backends, tmpdir=tmpdir,
        force_disabled=force_disabled, stop_on_failure=stop_on_failure,
        report_saving_strategy=report_saving_strategy
    )


def run_suite_class(suite_class, filter=None, fixtures=None, backends=[], tmpdir=None,
                    force_disabled=False, stop_on_failure=False, report_saving_strategy=None):
    suite = load_suite_from_class(suite_class)
    return run_suite(
        suite, fixtures=fixtures, backends=backends, tmpdir=tmpdir,
        force_disabled=force_disabled, stop_on_failure=stop_on_failure,
        report_saving_strategy=report_saving_strategy
    )


def wrap_func_into_suites(callback):
    @lcc.suite("My Suite")
    class MySuite:
        @lcc.test("Some test")
        def sometest(self):
            callback()

    return [MySuite]


def run_func_in_test(callback, tmpdir=None):
    return run_suite_classes(wrap_func_into_suites(callback), tmpdir=tmpdir)


def dump_report(report):
    try:
        import lxml
    except ImportError:
        pass
    else:
        xml = serialize_report_as_string(report)
        print(xml, file=sys.stderr)


def dummy_test_callback():
    def wrapped(suite):
        pass
    return wrapped


def run_main(args):
    events.reset()
    return main(args)
