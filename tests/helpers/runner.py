import os
import os.path as osp
import sys
import tempfile
import shutil

from lemoncheesecake.suite.loader import load_suites_from_classes, load_suite_from_file
from lemoncheesecake.suite import resolve_tests_dependencies
from lemoncheesecake import runner
from lemoncheesecake.events import AsyncEventManager
from lemoncheesecake.session import Session
from lemoncheesecake.reporting.backends.xml import serialize_report_as_string
from lemoncheesecake.fixture import FixtureRegistry, load_fixtures_from_func
from lemoncheesecake.project import create_project
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


def build_project_module(myproject_content):
    return """
import os.path
from lemoncheesecake.project import Project

# the class MyProject that inherits Project must be declared below:
{}

project = MyProject(os.path.dirname(__file__))
""".format(myproject_content)


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


def generate_project(project_dir, module_name, module_content, fixtures_content=None, project_content=None):
    create_project(project_dir)
    with open(osp.join(project_dir, "suites", "%s.py" % module_name), "w") as fh:
        fh.write(module_content)
    if fixtures_content:
        with open(osp.join(project_dir, "fixtures", "fixtures.py"), "w") as fh:
            fh.write(fixtures_content)
    if project_content:
        with open(osp.join(project_dir, "project.py"), "w") as fh:
            fh.write(project_content)


def build_fixture_registry(*funcs):
    registry = FixtureRegistry()
    for func in funcs:
        registry.add_fixtures(load_fixtures_from_func(func))
    return registry


def run_suites(suites, fixtures=None, backends=None, tmpdir=None, force_disabled=False, stop_on_failure=False,
               report_saving_strategy=None, nb_threads=1):
    if fixtures is None:
        fixture_registry = FixtureRegistry()
    else:
        if isinstance(fixtures, FixtureRegistry):
            fixture_registry = fixtures
        else:
            fixture_registry = build_fixture_registry(*fixtures)

    resolve_tests_dependencies(suites, suites)

    if backends is None:
        backends = []

    if tmpdir:
        report_dir = tmpdir if isinstance(tmpdir, str) else tmpdir.strpath
        session = Session.create(
            AsyncEventManager.load(), backends, report_dir, report_saving_strategy, nb_threads=nb_threads
        )
        runner.run_suites(
            suites, fixture_registry, session,
            force_disabled=force_disabled, stop_on_failure=stop_on_failure, nb_threads=nb_threads
        )
    else:
        report_dir = tempfile.mkdtemp()
        session = Session.create(
            AsyncEventManager.load(), backends, report_dir, report_saving_strategy, nb_threads=nb_threads
        )
        try:
            runner.run_suites(
                suites, fixture_registry, session,
                force_disabled=force_disabled, stop_on_failure=stop_on_failure, nb_threads=nb_threads
            )
        finally:
            shutil.rmtree(report_dir)

    dump_report(session.report)

    return session.report


def run_suite_classes(suite_classes, fixtures=None, backends=None, tmpdir=None,
                      force_disabled=False, stop_on_failure=False, report_saving_strategy=None, nb_threads=1):
    suites = load_suites_from_classes(suite_classes)
    return run_suites(
        suites, fixtures=fixtures, backends=backends, tmpdir=tmpdir,
        force_disabled=force_disabled, stop_on_failure=stop_on_failure,
        report_saving_strategy=report_saving_strategy, nb_threads=nb_threads
    )


def run_suite(suite, fixtures=None, backends=[], tmpdir=None, force_disabled=False, stop_on_failure=False,
              report_saving_strategy=None, nb_threads=1):
    return run_suites(
        [suite], fixtures=fixtures, backends=backends, tmpdir=tmpdir,
        force_disabled=force_disabled, stop_on_failure=stop_on_failure,
        report_saving_strategy=report_saving_strategy, nb_threads=nb_threads
    )


def run_suite_class(suite_class, fixtures=None, backends=[], tmpdir=None,
                    force_disabled=False, stop_on_failure=False, report_saving_strategy=None, nb_threads=1):
    suite = load_suite_from_class(suite_class)
    return run_suite(
        suite, fixtures=fixtures, backends=backends, tmpdir=tmpdir,
        force_disabled=force_disabled, stop_on_failure=stop_on_failure,
        report_saving_strategy=report_saving_strategy, nb_threads=nb_threads
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
    xml = serialize_report_as_string(report)
    print(xml, file=sys.stderr)


def dummy_test_callback():
    def wrapped(suite):
        pass
    return wrapped


def run_main(args):
    return main(args)
