import time
from functools import reduce

import pytest

from lemoncheesecake.task import BaseTask, TasksExecutionFailure, run_tasks, check_task_dependencies
from lemoncheesecake.exceptions import TaskFailure, CircularDependencyError


class BaseTestTask(BaseTask):
    def __init__(self, name, on_success_dependencies=None, on_completion_dependencies=None):
        BaseTask.__init__(self)
        self.name = name
        self.on_success_dependencies = on_success_dependencies or []
        self.on_completion_dependencies = on_completion_dependencies or []
        self.skipped = False
        self.exception_within_skip = None

    def get_on_success_dependencies(self):
        return self.on_success_dependencies

    def get_on_completion_dependencies(self):
        return self.on_completion_dependencies

    def skip(self, context, reason):
        self.skipped = True
        if self.exception_within_skip:
            raise self.exception_within_skip

    def __str__(self):
        return "<task %s>" % self.name

    def __repr__(self):
        return str(self)


class ExceptionTask(BaseTestTask):
    def __init__(self, name, exception, on_success_dependencies=None, on_completion_dependencies=None):
        BaseTestTask.__init__(self, name, on_success_dependencies, on_completion_dependencies)
        self._exception = exception
        self.skipped = False
        self.result = 0

    def run(self, context):
        raise self._exception


class DummyTask(BaseTestTask):
    def __init__(self, name, value, on_success_dependencies=None, on_completion_dependencies=None):
        BaseTestTask.__init__(self, name, on_success_dependencies, on_completion_dependencies)
        self.value = value
        self.result = None

    def run(self, context):
        time.sleep(0.001)
        self.result = reduce(
            lambda x, y: x + y,
            (dep.result for dep in self.on_success_dependencies + self.on_completion_dependencies),
            self.value
        )


def test_run_tasks_success():
    a = DummyTask("a", 1, [])
    b = DummyTask("b", 2, [a])
    c = DummyTask("c", 3, [a])
    d = DummyTask("d", 4, [b, c])

    run_tasks((a, b, c, d), nb_threads=1)

    assert d.result == 11


def test_run_tasks_failure_1():
    a = ExceptionTask("a", TaskFailure(), [])
    b = DummyTask("b", 2, [a])
    c = DummyTask("c", 3, [a])
    d = DummyTask("d", 4, [b, c])

    run_tasks((a, b, c, d), nb_threads=1)

    assert not a.skipped
    assert b.skipped
    assert c.skipped
    assert d.skipped


def test_run_tasks_failure_2():
    a = DummyTask("a", 1, [])
    b = DummyTask("b", 2, [a])
    c = ExceptionTask("c", TaskFailure(), [a])
    d = DummyTask("d", 4, [b, c])

    run_tasks((a, b, c, d), nb_threads=1)

    assert not a.skipped
    assert not b.skipped
    assert not c.skipped
    assert d.skipped


def test_run_tasks_unexpected_exception_in_run():
    a = DummyTask("a", 1, [])
    b = DummyTask("b", 2, [a])
    c = ExceptionTask("c", Exception("something bad happened"), [a])
    d = DummyTask("d", 4, [b, c])

    with pytest.raises(TasksExecutionFailure) as excinfo:
        run_tasks((a, b, c, d), nb_threads=1)

    assert "something bad happened" in str(excinfo.value)

    assert not a.skipped
    assert not b.skipped
    assert not c.skipped
    assert d.skipped


def test_run_tasks_unexpected_exception_in_abort():
    a = DummyTask("a", 1, [])
    b = DummyTask("b", 2, [a])
    c = ExceptionTask("c", TaskFailure(), [a])
    d = DummyTask("d", 4, [b, c])
    d.exception_within_skip = Exception("something bad happened")

    with pytest.raises(TasksExecutionFailure) as excinfo:
        run_tasks((a, b, c, d), nb_threads=1)

    assert "something bad happened" in str(excinfo.value)

    assert not a.skipped
    assert not b.skipped
    assert not c.skipped
    assert d.skipped


def test_run_tasks_using_on_completion_dependency_1():
    a = ExceptionTask("a", TaskFailure())
    b = DummyTask("b", 1, on_completion_dependencies=[a])

    run_tasks((a, b))

    assert not a.skipped
    assert b.result == 1


def test_run_tasks_using_on_completion_dependency_2():
    a = DummyTask("a", 1)
    b = DummyTask("b", 1, on_completion_dependencies=[a])

    run_tasks((a, b))

    assert a.successful and b.successful
    assert b.result == 2


def test_run_tasks_using_on_completion_dependency_3():
    a = ExceptionTask("a", TaskFailure())
    b = DummyTask("b", 1)
    c = DummyTask("c", 1, on_completion_dependencies=[a, b])

    run_tasks((a, b, c))

    assert not a.skipped
    assert b.successful
    assert c.result == 2


def test_run_tasks_using_on_completion_dependency_4():
    a = ExceptionTask("a", TaskFailure())
    b = ExceptionTask("b", TaskFailure())
    c = DummyTask("c", 1, on_completion_dependencies=[a], on_success_dependencies=[b])

    run_tasks((a, b, c))

    assert a.successful is False and b.successful is False
    assert c.skipped


def test_run_tasks_using_on_completion_dependency_5():
    a = ExceptionTask("a", TaskFailure())
    b = ExceptionTask("b", TaskFailure(), on_completion_dependencies=[a])
    c = DummyTask("c", 1, on_success_dependencies=[b])

    run_tasks((a, b, c))

    assert a.successful is False and b.successful is False
    assert c.skipped


def test_check_task_dependencies_ok():
    a = DummyTask("a", 1, [])
    b = DummyTask("b", 2, [a])

    check_task_dependencies(b)


def test_check_task_dependencies_ok_complex():
    a = DummyTask("a", 1, [])
    b = DummyTask("b", 2, [a])
    c = DummyTask("c", 3, [a])
    d = DummyTask("d", 4, [b, c])

    check_task_dependencies(d)


def test_check_task_dependencies_ko_direct_dependency():
    a = DummyTask("a", 1, [])
    b = DummyTask("b", 2, [a])
    a.on_success_dependencies.append(b)

    with pytest.raises(CircularDependencyError):
        check_task_dependencies(b)


def test_check_task_dependencies_ko_indirect_dependency():
    a = DummyTask("a", 1, [])
    b = DummyTask("b", 2, [a])
    c = DummyTask("c", 3, [b])
    a.on_success_dependencies.append(c)

    with pytest.raises(CircularDependencyError):
        check_task_dependencies(c)


def test_check_task_dependencies_ko_indirect_dependency_2():
    a = DummyTask("a", 1, [])
    b = DummyTask("b", 2, [a])
    c = DummyTask("c", 3, [b])
    a.on_success_dependencies.append(b)

    with pytest.raises(CircularDependencyError):
        check_task_dependencies(c)
