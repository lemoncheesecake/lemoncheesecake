import time
import re
import inspect

from lemoncheesecake.utils import camel_case_to_snake_case


def _get_event_name_from_class_name(class_name):
    return re.sub("_event$", "", camel_case_to_snake_case(class_name))


class Event(object):
    def __init__(self):
        self.time = time.time()

    @classmethod
    def get_name(cls):
        return _get_event_name_from_class_name(cls.__name__)


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

    def fire(self, event):
        for handler in self._handlers:
            handler(event)


def _get_event_name(val):
    return val.get_name() if inspect.isclass(val) and issubclass(val, Event) else val


class EventManager:
    def __init__(self):
        self._event_types = {}

    def register_events(self, *event_classes):
        for event_class in event_classes:
            self._event_types[event_class.get_name()] = EventType(event_class)

    def reset(self, event_name=None):
        if event_name is None:
            for event_type in self._event_types.values():
                event_type.reset()
        else:
            self._event_types[event_name].reset()

    def subscribe_to_event(self, event, handler):
        self._event_types[_get_event_name(event)].subscribe(handler)

    def subscribe_to_events(self, event_handler_pairs):
        for event, handler in event_handler_pairs.items():
            self.subscribe_to_event(event, handler)

    def add_listener(self, listener):
        for event_name in self._event_types:
            handler_name = "on_%s" % event_name
            handler = getattr(listener, handler_name, None)
            if handler and callable(handler):
                self.subscribe_to_event(event_name, handler)

    def unsubscribe_from_event(self, event, handler):
        self._event_types[_get_event_name(event)].unsubscribe(handler)

    def fire(self, event):
        self._event_types[event.__class__.get_name()].fire(event)


eventmgr = EventManager()
register_event = eventmgr.register_events
register_events = eventmgr.register_events
subscribe_to_event = eventmgr.subscribe_to_event
subscribe_to_events = eventmgr.subscribe_to_events
unsubscribe_from_event = eventmgr.unsubscribe_from_event
add_listener = eventmgr.add_listener
reset = eventmgr.reset
fire = eventmgr.fire


###
# Events related to the test session
###

class _ReportEvent(Event):
    def __init__(self, report):
        super(_ReportEvent, self).__init__()
        self.report = report


class TestSessionStartEvent(_ReportEvent):
    pass


class TestSessionEndEvent(_ReportEvent):
    pass


class TestSessionSetupStartEvent(Event):
    pass


class TestSessionSetupEndEvent(Event):
    def __init__(self, outcome):
        super(TestSessionSetupEndEvent, self).__init__()
        self.setup_outcome = outcome


class TestSessionTeardownStartEvent(Event):
    pass


class TestSessionTeardownEndEvent(Event):
    def __init__(self, outcome):
        super(TestSessionTeardownEndEvent, self).__init__()
        self.teardown_outcome = outcome


register_events(
    TestSessionStartEvent, TestSessionEndEvent,
    TestSessionSetupStartEvent, TestSessionSetupEndEvent,
    TestSessionTeardownStartEvent, TestSessionTeardownEndEvent
)


###
# Suite events
###

class _SuiteEvent(Event):
    def __init__(self, suite):
        super(_SuiteEvent, self).__init__()
        self.suite = suite


class SuiteStartEvent(_SuiteEvent):
    pass


class SuiteEndEvent(_SuiteEvent):
    pass


class SuiteSetupStartEvent(_SuiteEvent):
    pass


class SuiteSetupEndEvent(_SuiteEvent):
    def __init__(self, suite, outcome):
        super(SuiteSetupEndEvent, self).__init__(suite)
        self.setup_outcome = outcome


class SuiteTeardownStartEvent(_SuiteEvent):
    pass


class SuiteTeardownEndEvent(_SuiteEvent):
    def __init__(self, suite, outcome):
        super(SuiteTeardownEndEvent, self).__init__(suite)
        self.teardown_outcome = outcome


register_events(
    SuiteStartEvent, SuiteEndEvent,
    SuiteSetupStartEvent, SuiteSetupEndEvent,
    SuiteTeardownStartEvent, SuiteTeardownEndEvent
)


###
# Test events
###

class _TestEvent(Event):
    def __init__(self, test):
        super(_TestEvent, self).__init__()
        self.test = test


class TestStartEvent(_TestEvent):
    pass


class TestEndEvent(_TestEvent):
    def __init__(self, test, status):
        super(TestEndEvent, self).__init__(test)
        self.test_status = status


class TestSkippedEvent(_TestEvent):
    def __init__(self, test, reason):
        super(TestSkippedEvent, self).__init__(test)
        self.skipped_reason = reason


class TestDisabledEvent(_TestEvent):
    def __init__(self, test, reason):
        super(TestDisabledEvent, self).__init__(test)
        self.disabled_reason = reason


class TestSetupStartEvent(_TestEvent):
    pass


class TestSetupEndEvent(_TestEvent):
    def __init__(self, test, outcome):
        super(TestSetupEndEvent, self).__init__(test)
        self.setup_outcome = outcome


class TestTeardownStartEvent(_TestEvent):
    pass


class TestTeardownEndEvent(_TestEvent):
    def __init__(self, test, outcome):
        super(TestTeardownEndEvent, self).__init__(test)
        self.teardown_outcome = outcome


register_events(
    TestStartEvent, TestEndEvent, TestSkippedEvent, TestDisabledEvent,
    TestSetupStartEvent, TestSetupEndEvent,
    TestTeardownStartEvent, TestTeardownEndEvent
)


###
# Transverse test execution events
###

class StepEvent(Event):
    def __init__(self, description):
        super(StepEvent, self).__init__()
        self.step_description = description


class LogEvent(Event):
    def __init__(self, level, message):
        super(LogEvent, self).__init__()
        self.log_level = level
        self.log_message = message


class CheckEvent(Event):
    def __init__(self, description, outcome, details=None):
        super(CheckEvent, self).__init__()
        self.check_description = description
        self.check_outcome = outcome
        self.check_details = details


class LogAttachmentEvent(Event):
    def __init__(self, path, filename, description):
        super(LogAttachmentEvent, self).__init__()
        self.attachment_path = path
        self.attachment_filename = filename
        self.attachment_description = description


class LogUrlEvent(Event):
    def __init__(self, url, description):
        super(LogUrlEvent, self).__init__()
        self.url = url
        self.url_description = description


register_events(
    StepEvent, LogEvent, CheckEvent, LogAttachmentEvent, LogUrlEvent
)
