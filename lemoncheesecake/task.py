import sys
from multiprocessing.dummy import Pool, Queue

from lemoncheesecake.exceptions import AbortTask, TasksExecutionFailure, CircularDependencyError, \
    serialize_current_exception


class BaseTask(object):
    def __init__(self):
        self.successful = None
        self.exception = None

    def get_dependencies(self):
        return set()

    def run(self, context):
        pass

    def abort(self, context):
        pass


def pop_runnable_tasks(remaining_tasks, completed_tasks, nb_tasks):
    runnable_tasks = [task for task in remaining_tasks if set(task.get_dependencies()).issubset(completed_tasks)]
    runnable_tasks_by_priority = sorted(runnable_tasks, key=lambda task: len(task.get_dependencies()), reverse=True)

    for task in runnable_tasks_by_priority[:nb_tasks]:
        remaining_tasks.remove(task)
        yield task


def pop_dependant_tasks(ref_task, tasks):
    for task in list(tasks):
        if ref_task in task.get_dependencies():
            tasks.remove(task)
            yield task
            for indirect_task in pop_dependant_tasks(task, tasks):
                yield indirect_task


def run_task(task, context, completed_task_queue):
    try:
        task.run(context)
    except AbortTask:
        task.successful = False
    except Exception:
        task.successful = False
        task.exception = serialize_current_exception()
    else:
        task.successful = True

    completed_task_queue.put(task)


def do_run_tasks(tasks, context, pool, completed_tasks_queue):
    for task in tasks:
        pool.apply_async(run_task, args=(task, context, completed_tasks_queue))


def abort_task(task, context, completed_task_queue):
    try:
        task.abort(context)
    except Exception:
        task.successful = False
        task.exception = serialize_current_exception()
    else:
        task.successful = True

    completed_task_queue.put(task)


def abort_tasks(tasks, context, pool, completed_tasks_queue):
    for task in tasks:
        pool.apply_async(abort_task, args=(task, context, completed_tasks_queue))


def abort_all_tasks(tasks, remaining_tasks, completed_tasks, context, pool, completed_tasks_queue):
    abort_tasks(remaining_tasks, context, pool, completed_tasks_queue)
    while len(completed_tasks) != len(tasks):
        completed_task = completed_tasks_queue.get()
        completed_tasks.append(completed_task)


def run_tasks(tasks, context=None, nb_threads=1, watchdog=None):
    for task in tasks:
        check_task_dependencies(task)

    remaining_tasks = list(tasks)
    completed_tasks = list()

    pool = Pool(nb_threads)
    completed_tasks_queue = Queue()

    try:
        do_run_tasks(pop_runnable_tasks(remaining_tasks, completed_tasks, nb_threads), context, pool, completed_tasks_queue)

        while len(completed_tasks) != len(tasks):
            # wait for one task to complete
            completed_task = completed_tasks_queue.get()
            completed_tasks.append(completed_task)

            # watchdog
            exception_class, exception_arg = watchdog() if watchdog else (None, None)
            if exception_class:
                abort_all_tasks(tasks, remaining_tasks, completed_tasks, context, pool, completed_tasks_queue)
                raise exception_class(exception_arg)

            # schedule next tasks depending on the completed task success
            if completed_task.successful:
                runnable_tasks = pop_runnable_tasks(remaining_tasks, completed_tasks, nb_threads)
                do_run_tasks(runnable_tasks, context, pool, completed_tasks_queue)
            else:
                abortable_tasks = pop_dependant_tasks(completed_task, remaining_tasks)
                abort_tasks(abortable_tasks, context, pool, completed_tasks_queue)

    except KeyboardInterrupt:
        abort_all_tasks(tasks, remaining_tasks, completed_tasks, context, pool, completed_tasks_queue)

    finally:
        pool.close()

    if any(task.exception for task in tasks):
        raise TasksExecutionFailure(
            "Caught exceptions:\n%s" % "\n".join(task.exception for task in tasks if task.exception)
        )


def check_task_dependencies(task, task_path=()):
    for task_in_path in task_path:
        if task_in_path in task.get_dependencies():
            raise CircularDependencyError("Task %s has a circular dependency on task %s" % (task, task_in_path))

    for dependency in task.get_dependencies():
        check_task_dependencies(dependency, task_path=(task,) + task_path)
