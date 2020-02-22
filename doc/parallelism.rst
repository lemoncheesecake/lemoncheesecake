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