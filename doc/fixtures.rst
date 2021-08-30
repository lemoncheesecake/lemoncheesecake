.. _fixtures:

Fixtures
========

lemoncheesecake provides a fixture system similar to what `pytest <https://pytest.org>`_ offers
(http://doc.pytest.org/en/latest/fixture.html).
Fixtures are a powerful and modular way to inject dependencies into your tests.

.. code-block:: python

    # fixtures/myfixtures.py:

    import requests
    import lemoncheesecake.api as lcc

    @lcc.fixture(scope="session")
    def user_auth(cli_args):
        # we assume that custom cli arguments "user" and "password" have been
        # previously set through project file
        return cli_args.user, cli_args.password

    @lcc.fixture(scope="session")
    def api(user_auth):
        session = requests.Session()
        session.auth = user_auth
        return session

    # suites/my_suite.py:

    import lemoncheesecake.api as lcc

    SUITE = {
        "description": "My Suite"
    }

    @lcc.test("Some test")
    def some_test(api):
        resp = api.get("GET", "/some/resource")
        [...]

Fixtures can be injected into suites through parameters passed to ``setup_suite`` and class instance / module attributes:

.. code-block:: python

    # suites/my_suite.py:

    import lemoncheesecake.api as lcc

    SUITE = {
        "description": "My Suite"
    }

    def setup_suite(api):
        [...]

    # tests/my_suite.py:

    import lemoncheesecake.api as lcc

    SUITE = {
        "description": "My Suite"
    }

    api = lcc.inject_fixture()

Fixtures with scope ``pre_run`` that have been previously executed through a dependency can get be retrieved
using ``lcc.get_fixture(name)``.


Four fixture scopes are available (higher to lower scope):

- ``pre_run``: fixtures with this scope will be called before the test session is started, meaning that the
  fixture cannot use any of the ``log_*``, ``check_*``, etc... functions. If a fixture with this scope
  raises an exception, it will prevent the tests to be executed. This behavior can be used in conjunction with
  the ``UserError`` exception and the ``cli_args`` fixture to handle bad CLI arguments

- ``session``: fixtures with this scope are initialized at the global level

- ``suite``: fixtures with this scope are initialized at the test suite level; if a suite "A" uses a ``suite``
  scoped fixture (through a test for example), and a sub suite "B" uses the same fixture, then the fixture is
  initialized two times: one time for "A" and the other time for "B"

- ``test``: fixtures with this scope are initialized at the test level

Please note that:

- a fixture can be called through multiple names specified in the ``names`` parameter (otherwise the fixture name
  is the fixture function name):

  .. code-block:: python

      @lcc.fixture(names=("fixt_a", "fixt_b"))
      def fixt():
          [...]

- fixture teardown can be implemented using yield to initially return the fixture value and then to
  de-initialize the fixture:

  .. code-block:: python

      @lcc.fixture()
      def resource_file():
          fh = open("/some/file", "r")
          yield fh
          fh.close()

- a fixture can use other fixtures as arguments, in this case the scope level compatibility must be respected:
  for example, a ``test`` scoped fixture can use a ``session`` scoped fixture, but the opposite is not true

lemoncheesecake provides several special builtin fixtures:

- ``cli_args`` (scope: ``pre_run``) is the object returned by ``parse_args`` of the
  `argparse <https://docs.python.org/2/library/argparse.html>`_ module and that contains the actual CLI arguments;
  this fixture can be used to access custom command line arguments previously setup by the method ``add_custom_cli_args``
  of the project class declared in the lemoncheesecake project file

- ``project_dir`` (scope: ``pre_run``) is the path of the project, meaning the directory of the project file

- ``fixture_name`` is the name of the called fixture and can only be used by a fixture. A typical use case is a
  fixture with multiple names, ``fixture_name`` can be used to identify through which name the fixture has been called
  and adapts its behavior accordingly

Using the default ``project.py`` file, fixtures will be loaded from the ``fixtures`` sub directory.
