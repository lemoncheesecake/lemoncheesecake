from multiprocessing.dummy import Pool, Queue

from lemoncheesecake.exceptions import TaskFailure, TasksExecutionFailure, CircularDependencyError, \
    serialize_current_exception

_KEYBOARD_INTERRUPT_ERROR_MESSAGE = "all tests have been interrupted by the user"


class BaseTask(object):
    def __init__(self):
        self.successful = None
        self.exception = None

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
    runnable_tasks = [
        task for task in remaining_tasks if set(task.get_all_dependencies()).issubset(completed_tasks)
    ]
    # return the tasks with the greater number of dependencies first
    runnable_tasks_by_priority = sorted(
        runnable_tasks, key=lambda task: len(task.get_all_dependencies()), reverse=True
    )

    for task in runnable_tasks_by_priority[:nb_tasks]:
        remaining_tasks.remove(task)
        yield task


def pop_skippable_tasks(ref_task, tasks):
    for task in list(tasks):
        if ref_task in task.get_on_success_dependencies() and task in tasks:
            tasks.remove(task)
            yield task
            for indirect_task in pop_skippable_tasks(task, tasks):
                yield indirect_task


def run_task(task, context, completed_task_queue):
    try:
        task.run(context)
    except TaskFailure:
        task.successful = False
    except Exception:
        task.successful = False
        task.exception = serialize_current_exception()
    else:
        task.successful = True

    completed_task_queue.put(task)


def handle_task(task, watchdogs, context, completed_task_queue):
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
    try:
        task.skip(context, reason)
    except Exception:
        task.successful = False
        task.exception = serialize_current_exception()
    else:
        task.successful = True

    completed_task_queue.put(task)


def schedule_tasks_to_be_skipped(tasks, context, pool, completed_tasks_queue, reason=""):
    for task in tasks:
        pool.apply_async(skip_task, args=(task, context, completed_tasks_queue, reason))


def skip_all_tasks(tasks, remaining_tasks, completed_tasks, context, pool, completed_tasks_queue, reason):
    schedule_tasks_to_be_skipped(remaining_tasks, context, pool, completed_tasks_queue, reason)
    while len(completed_tasks) != len(tasks):
        completed_task = completed_tasks_queue.get()
        completed_tasks.append(completed_task)


def run_tasks(tasks, context=None, nb_threads=1, watchdog=None):
    got_keyboard_interrupt = False
    watchdogs = [lambda _: _KEYBOARD_INTERRUPT_ERROR_MESSAGE if got_keyboard_interrupt else None]
    if watchdog:
        watchdogs.append(watchdog)

    for task in tasks:
        check_task_dependencies(task)

    remaining_tasks = list(tasks)
    completed_tasks = list()

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
            completed_tasks.append(completed_task)

            # schedule tasks to be skipped after task failure
            if not completed_task.successful:
                tasks_to_be_skipped = pop_skippable_tasks(completed_task, remaining_tasks)
                schedule_tasks_to_be_skipped(tasks_to_be_skipped, context, pool, completed_tasks_queue)

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

    if any(task.exception for task in tasks):
        raise TasksExecutionFailure(
            "Caught exceptions:\n%s" % "\n".join(task.exception for task in tasks if task.exception)
        )


def check_task_dependencies(task, task_path=()):
    for task_in_path in task_path:
        if task_in_path in task.get_all_dependencies():
            raise CircularDependencyError("Task %s has a circular dependency on task %s" % (task, task_in_path))

    for dependency in task.get_all_dependencies():
        check_task_dependencies(dependency, task_path=(task,) + task_path)
