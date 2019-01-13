import time
from functools import reduce

import pytest

from lemoncheesecake.task import BaseTask, TasksExecutionFailure, run_tasks, check_task_dependencies
from lemoncheesecake.exceptions import TaskFailure, CircularDependencyError


class BaseTestTask(BaseTask):
    def __init__(self, name, dependencies=()):
        BaseTask.__init__(self)
        self.name = name
        self.dependencies = list(dependencies)
        self.aborted = False
        self.exception_within_abort = None

    def get_dependencies(self):
        return set(self.dependencies)

    def skip(self, context, reason):
        self.aborted = True
        if self.exception_within_abort:
            raise self.exception_within_abort

    def __str__(self):
        return "<task %s>" % self.name

    def __repr__(self):
        return str(self)


class ExceptionTask(BaseTestTask):
    def __init__(self, name, exception, dependencies=()):
        BaseTestTask.__init__(self, name, dependencies)
        self._exception = exception
        self.aborted = False

    def run(self, context):
        raise self._exception


class DummyTask(BaseTestTask):
    def __init__(self, name, value, dependencies=()):
        BaseTestTask.__init__(self, name, dependencies)
        self.value = value
        self.result = None

    def run(self, context):
        time.sleep(0.001)
        self.result = reduce(lambda x, y: x + y, (dep.result for dep in self.dependencies), self.value)


def test_run_tasks_success():
    a = DummyTask("a", 1)
    b = DummyTask("b", 2, (a,))
    c = DummyTask("c", 3, (a,))
    d = DummyTask("d", 4, (b, c))

    run_tasks((a, b, c, d), nb_threads=1)

    assert d.result == 11


def test_run_tasks_failure_1():
    a = ExceptionTask("a", TaskFailure())
    b = DummyTask("b", 2, (a,))
    c = DummyTask("c", 3, (a,))
    d = DummyTask("d", 4, (b, c))

    run_tasks((a, b, c, d), nb_threads=1)

    assert not a.aborted
    assert b.aborted
    assert c.aborted
    assert d.aborted


def test_run_tasks_failure_2():
    a = DummyTask("a", 1)
    b = DummyTask("b", 2, (a,))
    c = ExceptionTask("c", TaskFailure(), (a,))
    d = DummyTask("d", 4, (b, c))

    run_tasks((a, b, c, d), nb_threads=1)

    assert not a.aborted
    assert not b.aborted
    assert not c.aborted
    assert d.aborted


def test_run_tasks_unexpected_exception_in_run():
    a = DummyTask("a", 1)
    b = DummyTask("b", 2, (a,))
    c = ExceptionTask("c", Exception("something bad happened"), (a,))
    d = DummyTask("d", 4, (b, c))

    with pytest.raises(TasksExecutionFailure) as excinfo:
        run_tasks((a, b, c, d), nb_threads=1)

    assert "something bad happened" in str(excinfo.value)

    assert not a.aborted
    assert not b.aborted
    assert not c.aborted
    assert d.aborted


def test_run_tasks_unexpected_exception_in_abort():
    a = DummyTask("a", 1)
    b = DummyTask("b", 2, (a,))
    c = ExceptionTask("c", TaskFailure(), (a,))
    d = DummyTask("d", 4, (b, c))
    d.exception_within_abort = Exception("something bad happened")

    with pytest.raises(TasksExecutionFailure) as excinfo:
        run_tasks((a, b, c, d), nb_threads=1)

    assert "something bad happened" in str(excinfo.value)

    assert not a.aborted
    assert not b.aborted
    assert not c.aborted
    assert d.aborted


def test_check_task_dependencies_ok():
    a = DummyTask("a", 1)
    b = DummyTask("b", 2, (a,))

    check_task_dependencies(b)


def test_check_task_dependencies_ok_complex():
    a = DummyTask("a", 1)
    b = DummyTask("b", 2, (a,))
    c = DummyTask("c", 3, (a,))
    d = DummyTask("d", 4, (b, c))

    check_task_dependencies(d)


def test_check_task_dependencies_ko_direct_dependency():
    a = DummyTask("a", 1)
    b = DummyTask("b", 2, (a,))
    a.dependencies.append(b)

    with pytest.raises(CircularDependencyError):
        check_task_dependencies(b)


def test_check_task_dependencies_ko_indirect_dependency():
    a = DummyTask("a", 1)
    b = DummyTask("b", 2, (a,))
    c = DummyTask("c", 3, (b,))
    a.dependencies.append(c)

    with pytest.raises(CircularDependencyError):
        check_task_dependencies(c)


def test_check_task_dependencies_ko_indirect_dependency_2():
    a = DummyTask("a", 1)
    b = DummyTask("b", 2, (a,))
    c = DummyTask("c", 3, (b,))
    a.dependencies.append(b)

    with pytest.raises(CircularDependencyError):
        check_task_dependencies(c)
