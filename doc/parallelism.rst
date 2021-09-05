.. _parallelism:

Test parallelism
================

.. _run_parallel:

Running tests in parallel
-------------------------

lemoncheesecake can run tests in parallel using Python threads, meaning:

- your code shares a global state
- your code has to be thread safe

by default, tests are NOT parallelized.

They can be run in parallel using the ``--threads`` argument, which indicates the number of threads that will be used to
run tests:

.. code-block:: none

    $ lcc run --threads 5

The number of threads used to run tests can also be specified using the ``$LCC_THREADS`` environment variable.
The CLI argument has priority over the environment variable.

.. _threaded_factory:

Creating objects on a per-thread basis
--------------------------------------

.. versionadded:: 1.9.0

You may need to share objects between tests while not sharing them between threads because either there are not
thread-safe or simply because the underlying object is not intended to be used simultaneously (think for instance
to a web browser driven by a `selenium <https://selenium-python.readthedocs.io/>`_ web driver).

In this case, you may use :py:class:`ThreadedFactory <lemoncheesecake.api.ThreadedFactory>`.

Let's say you're writing tests with selenium. You want to parallelize tests and you want to avoid starting and quitting
a new browser for each test because it slows down the test run and you want your driver instance to be available across all
your test suite, then you could write something like this::

    # suites/suite.py

    import lemoncheesecake.api as lcc
    from selenium import webdriver


    class DriverFactory(lcc.ThreadedFactory):
        def setup_object(self):
            return webdriver.Firefox()

        def teardown_object(self, driver):
            driver.quit()


    @lcc.suite()
    class suite:
        def __init__(self):
            self.factory = DriverFactory()

        @property
        def driver(self):
            return self.factory.get_object()

        def teardown_suite(self):
            self.factory.teardown_factory()

        def some_helper_function(self):
            self.driver.do_something_useful(...)

        @lcc.test()
        def test_1().
            self.driver.get(...)
            [... do things ...]

        @lcc.test()
        def test_2().
            self.driver.get(...)
            [... do some other things ...]

        @lcc.test()
        def test_3().
            self.driver.get(...)
            self.some_helper_function()
            [... do some other things again ...]


By doing this, when ``self.driver`` (we implement the underlying object retrieval as a property to make it convenient to use)
is called directly or indirectly by a test, you are guaranteed that the object you'll get is
**not used by another thread at the same time** while this object will be
**reused between tests running on the same thread**.

We took selenium here as an example because this is a typical use case where tests parallelization + object sharing between tests
running on the same thread is quite useful, but it will work with any kind of object of course.

Please note that per-thread object sharing can also be achieved through
:ref:`per-thread fixtures <per_thread_fixtures>`. While they are not as flexible to use as the ``ThreadedFactory`` class,
they are more easy to use and should solve most of object sharing issues in parallelized tests environment.

Threading within tests
----------------------

.. _threads_in_test:

Threads can be used within a tests, for instance to test a remote service against concurrent accesses.
In this case, the thread instance must be created using ``lcc.Thread`` instead of ``threading.Thread``.
``lcc.Thread`` inherits ``threading.Thread`` and behaves the same way.

In order to avoid to mess up the test output by two threads logging in the same step, it is recommended to associate a
thread output to a dedicated step.

.. code-block:: python

    @lcc.test("Some test")
    def some_test():
        def func_1():
            lcc.set_step("Doing something in thread 1"):
            [..]

        def func_2():
            lcc.set_step("Doing something else in thread 2"):
            [..]

        thread_1 = lcc.Thread(target=func_1)
        thread_2 = lcc.Thread(target=func_2)

        thread_1.start()
        thread_2.start()

        thread_1.join()
        thread_2.join()

.. versionchanged:: 1.4.5

Prior to version to 1.4.5, it was required to use the ``lcc.detached_step`` context manager within new threads, like this::

    with lcc.detached_step("Doing something in thread")
        [...]

Since version 1.4.5, simply use ``lcc.set_step``. ``lcc.detached_step`` has been kept for backward-compatibility and is
now deprecated, all it does is to call ``lcc.set_step``.