import sys
import time
import re
import inspect
import threading
from contextlib import contextmanager

from six.moves.queue import Queue

from lemoncheesecake.helpers.text import camel_case_to_snake_case
from lemoncheesecake.exceptions import serialize_current_exception

DEBUG = False


class Event(object):
    def __init__(self, event_time=None):
        self.time = event_time or time.time()

    @classmethod
    def get_name(cls):
        return re.sub(r"_event$", "", camel_case_to_snake_case(cls.__name__))

    def __str__(self):
        return "<Event type='%s'>" % self.get_name()


class EventType:
    def __init__(self, event_class):
        self._event_class = event_class
        self._handlers = []

    def subscribe(self, handler):
        self._handlers.append(handler)

    def unsubscribe(self, handler):
        self._handlers.remove(handler)

    def reset(self):
        self._handlers = []

    def handle(self, event):
        for handler in self._handlers:
            handler(event)


class EventManager(object):
    def __init__(self):
        self._event_types = {}

    @staticmethod
    def _get_event_classes():
        """
        Get available event classes by introspecting this module to get available event classes.
        """
        current_module = sys.modules[__name__]
        for sym_name in dir(current_module):
            if sym_name.startswith("_"):
                continue
            sym = getattr(current_module, sym_name)
            if inspect.isclass(sym) and sym is not Event and issubclass(sym, Event):
                yield sym

    @classmethod
    def load(cls):
        eventmgr = cls()
        for event_class in eventmgr._get_event_classes():
            eventmgr.register_event(event_class)
        return eventmgr

    @staticmethod
    def _get_event_name(val):
        # val can be either an Event-based class or the name of the event itself (as an str)
        return val.get_name() if inspect.isclass(val) and issubclass(val, Event) else val

    def register_event(self, *event_classes):
        for event_class in event_classes:
            self._event_types[event_class.get_name()] = EventType(event_class)

    def subscribe_to_event(self, event, handler):
        self._event_types[self._get_event_name(event)].subscribe(handler)

    def subscribe_to_events(self, handlers):
        for event, handler in handlers.items():
            self.subscribe_to_event(event, handler)

    def add_listener(self, listener):
        for event_name in self._event_types:
            handler_name = "on_%s" % event_name
            handler = getattr(listener, handler_name, None)
            if handler and callable(handler):
                self.subscribe_to_event(event_name, handler)

    def unsubscribe_from_event(self, event, handler):
        self._event_types[self._get_event_name(event)].unsubscribe(handler)

    def handle_event(self, event):
        self._event_types[event.__class__.get_name()].handle(event)

    def fire(self, event):
        raise NotImplementedError()


class AsyncEventManager(EventManager):
    def __init__(self):
        EventManager.__init__(self)
        self._queue = None
        self._pending_failure = None, None

    def fire(self, event):
        assert self._queue, "Events can't be fired outside the 'handle_events' context manager."
        if DEBUG:
            print("Fire event %s" % event)
        self._queue.put(event)

    def get_pending_failure(self):
        return self._pending_failure

    def _handler_loop(self):
        while True:
            event = self._queue.get()
            if event is None:
                break
            try:
                self.handle_event(event)
            except Exception as excp:
                self._pending_failure = excp, serialize_current_exception()
                break
            finally:
                self._queue.task_done()

    @contextmanager
    def handle_events(self):
        self._queue = Queue()

        thread = threading.Thread(target=self._handler_loop)
        thread.start()

        try:
            yield
        finally:
            self._queue.put(None)
            thread.join()
            self._queue = None


class SyncEventManager(EventManager):
    def fire(self, event):
        if DEBUG:
            print("Fire event %s" % event)
        return self.handle_event(event)


###
# Events related to the test session
###

class _ReportEvent(Event):
    def __init__(self, report, event_time=None):
        super(_ReportEvent, self).__init__(event_time)
        self.report = report


class TestSessionStartEvent(_ReportEvent):
    pass


class TestSessionEndEvent(_ReportEvent):
    pass


class TestSessionSetupStartEvent(Event):
    pass


class TestSessionSetupEndEvent(Event):
    pass


class TestSessionTeardownStartEvent(Event):
    pass


class TestSessionTeardownEndEvent(Event):
    pass


###
# Suite events
###

class _SuiteEvent(Event):
    def __init__(self, suite, event_time=None):
        super(_SuiteEvent, self).__init__(event_time)
        self.suite = suite

    def __str__(self):
        return "<Event type='%s' suite='%s'>" % (self.get_name(), self.suite.path)


class SuiteStartEvent(_SuiteEvent):
    pass


class SuiteEndEvent(_SuiteEvent):
    pass


class SuiteSetupStartEvent(_SuiteEvent):
    pass


class SuiteSetupEndEvent(_SuiteEvent):
    pass


class SuiteTeardownStartEvent(_SuiteEvent):
    pass


class SuiteTeardownEndEvent(_SuiteEvent):
    pass


###
# Test events
###

class _TestEvent(Event):
    def __init__(self, test, event_time=None):
        super(_TestEvent, self).__init__(event_time)
        self.test = test

    def __str__(self):
        return "<Event type='%s' test='%s'>" % (self.get_name(), self.test.path)


class TestStartEvent(_TestEvent):
    pass


class TestEndEvent(_TestEvent):
    pass


class TestSkippedEvent(_TestEvent):
    def __init__(self, test, reason, event_time=None):
        super(TestSkippedEvent, self).__init__(test, event_time)
        self.skipped_reason = reason


class TestDisabledEvent(_TestEvent):
    def __init__(self, test, reason, event_time=None):
        super(TestDisabledEvent, self).__init__(test, event_time)
        self.disabled_reason = reason


###
# Transverse test execution events
###

class RuntimeEvent(Event):
    def __init__(self, location, event_time=None):
        super(RuntimeEvent, self).__init__(event_time)
        self.location = location


class StepStartEvent(RuntimeEvent):
    def __init__(self, location, description, thread_id, event_time=None):
        super(StepStartEvent, self).__init__(location, event_time)
        self.step_description = description
        self.thread_id = thread_id

    def __str__(self):
        return "<Event type='%s' description='%s'>" % (
            self.get_name(), self.step_description
        )


class StepEndEvent(RuntimeEvent):
    def __init__(self, location, step, thread_id, event_time=None):
        super(StepEndEvent, self).__init__(location, event_time)
        self.step = step
        self.thread_id = thread_id


class SteppedEvent(RuntimeEvent):
    """
    This event class cannot be instantiated directly and only serve has a base
    class for all events happening within a step.
    """
    def __init__(self, location, step, thread_id, event_time=None):
        super(SteppedEvent, self).__init__(location, event_time)
        self.step = step
        self.thread_id = thread_id


class LogEvent(SteppedEvent):
    def __init__(self, location, step, thread_id, level, message, event_time=None):
        super(LogEvent, self).__init__(location, step, thread_id, event_time)
        self.log_level = level
        self.log_message = message

    def __str__(self):
        return "<Event type='%s' level='%s' message='%s'>" % (
            self.get_name(), self.log_level, self.log_message
        )


class CheckEvent(SteppedEvent):
    def __init__(self, location, step, thread_id, description, is_successful, details=None, event_time=None):
        super(CheckEvent, self).__init__(location, step, thread_id, event_time)
        self.check_description = description
        self.check_is_successful = is_successful
        self.check_details = details

    def __str__(self):
        return "<Event type='%s' description='%s' details='%s' is_successful='%s'>" % (
            self.get_name(), self.check_description, self.check_details,
            "success" if self.check_is_successful else "failure"
        )


class LogAttachmentEvent(SteppedEvent):
    def __init__(self, location, step, thread_id, path, description, as_image, event_time=None):
        super(LogAttachmentEvent, self).__init__(location, step, thread_id, event_time)
        self.attachment_path = path
        self.attachment_description = description
        self.as_image = as_image

    def __str__(self):
        return "<Event type='%s' path='%s' description='%s'>" % (
            self.get_name(), self.attachment_path, self.attachment_description
        )


class LogUrlEvent(SteppedEvent):
    def __init__(self, location, step, thread_id, url, description, event_time=None):
        super(LogUrlEvent, self).__init__(location, step, thread_id, event_time)
        self.url = url
        self.url_description = description

    def __str__(self):
        return "<Event type='%s' url='%s' description='%s'>" % (
            self.get_name(), self.url, self.url_description
        )
