import itertools
from multiprocessing.dummy import Pool, Queue

from lemoncheesecake.exceptions import TaskFailure, TasksExecutionFailure, CircularDependencyError, \
    serialize_current_exception

DEBUG = 0
_KEYBOARD_INTERRUPT_ERROR_MESSAGE = "tests have been interrupted by the user"


def _debug(msg):
    if DEBUG:
        print(msg)


class TaskResultSuccess(object):
    pass


class TaskResultSkipped(object):
    pass


class TaskResultFailure(object):
    def __init__(self, reason):
        self.reason = reason


class TaskResultException(object):
    def __init__(self, stacktrace):
        self.stacktrace = stacktrace


class BaseTask(object):
    def __init__(self):
        self.result = None

    def get_all_dependencies(self):
        return self.get_on_completion_dependencies() + self.get_on_success_dependencies()

    def get_on_success_dependencies(self):
        return []

    def get_on_completion_dependencies(self):
        return []

    def run(self, context):
        pass

    def skip(self, context, reason):
        pass


def pop_runnable_tasks(remaining_tasks, completed_tasks, nb_tasks):
    runnable_tasks = list(
        itertools.islice(
            filter(lambda t: set(t.get_all_dependencies()).issubset(completed_tasks), remaining_tasks),
            0, nb_tasks
        )
    )

    for task in runnable_tasks:
        remaining_tasks.remove(task)
        _debug("pop runnable task %s" % task)
        yield task


def run_task(task, context, completed_task_queue):
    _debug("run task %s" % task)
    try:
        task.run(context)
    except TaskFailure as excp:
        task.result = TaskResultFailure(str(excp))
    except Exception:
        task.result = TaskResultException(serialize_current_exception())
    else:
        task.result = TaskResultSuccess()

    completed_task_queue.put(task)


def handle_task(task, watchdogs, context, completed_task_queue):
    _debug("handle task %s" % task)
    for dep_task in task.get_on_success_dependencies():
        if not isinstance(dep_task.result, TaskResultSuccess):
            reason = None
            if isinstance(dep_task.result, TaskResultFailure):
                reason = dep_task.result.reason
            skip_task(task, context, completed_task_queue, reason)
            return

    for watchdog in watchdogs:
        error = watchdog(task)
        if error:
            skip_task(task, context, completed_task_queue, reason=error)
            return

    run_task(task, context, completed_task_queue)


def schedule_tasks_to_be_run(tasks, watchdogs, context, pool, completed_tasks_queue):
    for task in tasks:
        pool.apply_async(handle_task, args=(task, watchdogs, context, completed_tasks_queue))


def skip_task(task, context, completed_task_queue, reason=""):
    _debug("skip task %s" % task)
    try:
        task.skip(context, reason)
    except Exception:
        task.result = TaskResultException(serialize_current_exception())
    else:
        task.result = TaskResultSkipped()

    completed_task_queue.put(task)


def schedule_tasks_to_be_skipped(tasks, context, pool, completed_tasks_queue, reason=""):
    for task in tasks:
        pool.apply_async(skip_task, args=(task, context, completed_tasks_queue, reason))


def skip_all_tasks(tasks, remaining_tasks, completed_tasks, context, pool, completed_tasks_queue, reason):
    schedule_tasks_to_be_skipped(remaining_tasks, context, pool, completed_tasks_queue, reason)
    while len(completed_tasks) != len(tasks):
        completed_task = completed_tasks_queue.get()
        completed_tasks.add(completed_task)


def run_tasks(tasks, context=None, nb_threads=1, watchdog=None):
    got_keyboard_interrupt = False
    watchdogs = [lambda _: _KEYBOARD_INTERRUPT_ERROR_MESSAGE if got_keyboard_interrupt else None]
    if watchdog:
        watchdogs.append(watchdog)

    for task in tasks:
        check_task_dependencies(task)

    remaining_tasks = list(tasks)
    completed_tasks = set()

    pool = Pool(nb_threads)
    completed_tasks_queue = Queue()

    try:
        schedule_tasks_to_be_run(
            pop_runnable_tasks(remaining_tasks, completed_tasks, nb_threads),
            watchdogs, context, pool, completed_tasks_queue
        )

        while len(completed_tasks) != len(tasks):
            # wait for one task to complete
            completed_task = completed_tasks_queue.get()
            completed_tasks.add(completed_task)

            # schedule tasks to be run waiting for task success or simple completion
            tasks_to_be_run = pop_runnable_tasks(remaining_tasks, completed_tasks, nb_threads)
            schedule_tasks_to_be_run(tasks_to_be_run, watchdogs, context, pool, completed_tasks_queue)

    except KeyboardInterrupt:
        got_keyboard_interrupt = True
        skip_all_tasks(
            tasks, remaining_tasks, completed_tasks, context, pool, completed_tasks_queue,
            _KEYBOARD_INTERRUPT_ERROR_MESSAGE
        )

    finally:
        pool.close()

    exceptions = [task.result.stacktrace for task in tasks if isinstance(task.result, TaskResultException)]
    if exceptions:
        raise TasksExecutionFailure("Caught exceptions:\n%s" % "\n".join(exceptions))


def check_task_dependencies(task, task_path=()):
    for task_in_path in task_path:
        if task_in_path in task.get_all_dependencies():
            raise CircularDependencyError("Task %s has a circular dependency on task %s" % (task, task_in_path))

    for dependency in task.get_all_dependencies():
        check_task_dependencies(dependency, task_path=(task,) + task_path)
