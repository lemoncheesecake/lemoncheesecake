import itertools
from multiprocessing.dummy import Pool, Queue

from lemoncheesecake.exceptions import LemoncheesecakeException, TaskFailure, serialize_current_exception

DEBUG = False
_KEYBOARD_INTERRUPT_ERROR_MESSAGE = "tests have been interrupted by the user"


def _debug(msg):
    if DEBUG:
        print(msg)


class TaskResultSuccess(object):
    pass


class TaskResultSkipped(object):
    def __init__(self, reason):
        self.reason = reason


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


class TaskContext(object):
    def __init__(self):
        self._tasks_aborted = False

    def enable_task_abort(self):
        self._tasks_aborted = True

    def is_task_to_be_skipped(self, task):
        if self._tasks_aborted:
            return "tests have been manually stopped"
        else:
            return None


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


def handle_task(task, context, completed_task_queue):
    _debug("handle task %s" % task)

    # skip task on dependency failure if any
    for dep_task in task.get_on_success_dependencies():
        if not isinstance(dep_task.result, TaskResultSuccess):
            if isinstance(dep_task.result, (TaskResultFailure, TaskResultSkipped)):
                reason = dep_task.result.reason
            else:
                reason = None
            skip_task(task, context, completed_task_queue, reason)
            return

    # skip task on external trigger if any
    skip_reason = context.is_task_to_be_skipped(task)
    if skip_reason:
        skip_task(task, context, completed_task_queue, reason=skip_reason)
        return

    # run task when all conditions are met
    run_task(task, context, completed_task_queue)


def schedule_tasks_to_be_run(tasks, context, pool, completed_tasks_queue):
    for task in tasks:
        pool.apply_async(handle_task, args=(task, context, completed_tasks_queue))


def skip_task(task, context, completed_task_queue, reason=""):
    _debug("skip task %s" % task)
    try:
        task.skip(context, reason)
    except Exception:
        task.result = TaskResultException(serialize_current_exception())
    else:
        task.result = TaskResultSkipped(reason)

    completed_task_queue.put(task)


def skip_all_tasks(tasks, remaining_tasks, completed_tasks, context, pool, completed_tasks_queue, reason):
    # schedule all tasks to be skipped...
    for task in remaining_tasks:
        pool.apply_async(skip_task, args=(task, context, completed_tasks_queue, reason))

    # ... and wait for their completion
    while len(completed_tasks) != len(tasks):
        completed_task = completed_tasks_queue.get()
        completed_tasks.add(completed_task)


def run_tasks(tasks, context, nb_threads=1):
    for task in tasks:
        check_task_dependencies(task)

    remaining_tasks = list(tasks)
    completed_tasks = set()

    pool = Pool(nb_threads)
    completed_tasks_queue = Queue()

    try:
        schedule_tasks_to_be_run(
            pop_runnable_tasks(remaining_tasks, completed_tasks, nb_threads),
            context, pool, completed_tasks_queue
        )

        while len(completed_tasks) != len(tasks):
            # wait for one task to complete
            completed_task = completed_tasks_queue.get()
            completed_tasks.add(completed_task)

            # schedule tasks to be run waiting for task success or simple completion
            tasks_to_be_run = pop_runnable_tasks(remaining_tasks, completed_tasks, nb_threads)
            schedule_tasks_to_be_run(tasks_to_be_run, context, pool, completed_tasks_queue)

    except KeyboardInterrupt:
        context.enable_task_abort()
        skip_all_tasks(
            tasks, remaining_tasks, completed_tasks, context, pool, completed_tasks_queue,
            _KEYBOARD_INTERRUPT_ERROR_MESSAGE
        )

    finally:
        pool.close()

    exceptions = [task.result.stacktrace for task in tasks if isinstance(task.result, TaskResultException)]
    if exceptions:
        raise LemoncheesecakeException(
            "Error(s) while running tasks, got exceptions:\n%s" % "\n".join(exceptions)
        )


def check_task_dependencies(task, task_path=()):
    for task_in_path in task_path:
        if task_in_path in task.get_all_dependencies():
            raise AssertionError("Task %s has a circular dependency on task %s" % (task, task_in_path))

    for dependency in task.get_all_dependencies():
        check_task_dependencies(dependency, task_path=(task,) + task_path)
