import os.path

import pytest

from lemoncheesecake.fixture import load_fixtures_from_file, load_fixtures_from_files, load_fixtures_from_directory

@pytest.fixture()
def dir_with_fixtures(tmpdir):
    module_content = """import lemoncheesecake.api as lcc

@lcc.fixture()
def bar():
    pass

@lcc.fixture()
def foo(bar):
    pass

def baz():
    pass
"""

    file = tmpdir.join("myfixtures.py")
    file.write(module_content)
    return tmpdir.strpath


def test_load_fixture_from_file(dir_with_fixtures):
    fixtures = load_fixtures_from_file(os.path.join(dir_with_fixtures, "myfixtures.py"))

    assert len(fixtures) == 2
    assert fixtures[0].name == "bar"
    assert fixtures[0].scope == "test"
    assert fixtures[1].name == "foo"
    assert fixtures[1].scope == "test"


def test_load_fixture_from_files(dir_with_fixtures):
    fixtures = load_fixtures_from_files(os.path.join(dir_with_fixtures, "*.py"))

    assert len(fixtures) == 2


def test_load_fixture_from_dir(dir_with_fixtures):
    fixtures = load_fixtures_from_directory(dir_with_fixtures)

    assert len(fixtures) == 2