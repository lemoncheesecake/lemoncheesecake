import time

from lemoncheesecake.utils import get_callable_args
from lemoncheesecake.exceptions import NoSuchEventType, MismatchingEventArguments
from lemoncheesecake.suite import Suite, Test
from lemoncheesecake.reporting.report import Report


class EventType:
    def __init__(self, event_type_name, event_arg_types):
        self._event_type_name = event_type_name
        self._event_arg_types = event_arg_types
        self._handlers = []

    def _has_extra_time_arg(self, args):
        return (len(args) == len(self._event_arg_types) + 1) and args[-1].endswith("time")

    def subscribe(self, handler):
        handler_args = get_callable_args(handler)

        handler_args_number = len(handler_args) - (1 if self._has_extra_time_arg(handler_args) else 0)
        if handler_args_number != len(self._event_arg_types):
            raise MismatchingEventArguments(
                "For event type '%s', expecting %d arguments, got %d in handler %s (not counting possible extra event_time argument)" % (
                    self._event_type_name, len(self._event_arg_types), handler_args_number, handler
            ))

        if self._has_extra_time_arg(handler_args):
            assert len(handler_args) == len(self._event_arg_types) + 1
        else:
            assert len(handler_args) == len(self._event_arg_types)

        self._handlers.append(handler)

    def unsubscribe(self, handler):
        self._handlers.remove(handler)

    def reset(self):
        self._handlers = []

    def _handle_event(self, handler, args, event_time):
        handler_expected_args = get_callable_args(handler)
        handler_args = list(args)
        if self._has_extra_time_arg(handler_expected_args):
            handler_args.append(event_time)
        handler(*handler_args)

    def fire(self, *args, **kwargs):
        event_time = kwargs.get("event_time") or time.time()

        # check that fire is called with the proper number of arguments
        if len(args) != len(self._event_arg_types):
            raise MismatchingEventArguments("For event type '%s', expecting %d arguments, got %d" % (
                self._event_type_name, len(self._event_arg_types), len(args)
            ))

        # check that fire is called with the appropriate argument types
        i = 0
        for handler_arg, event_arg in zip(args, self._event_arg_types):
            if (handler_arg is not None) and (not isinstance(handler_arg, event_arg)):
                raise MismatchingEventArguments("For event type '%s', expecting type '%s' for argument #%d, got '%s'" % (
                    self._event_type_name, event_arg, i+1, type(handler_arg)
                ))
            i += 1

        # call handlers
        for handler in self._handlers:
            self._handle_event(handler, args, event_time)


class EventManager:
    def __init__(self):
        self._event_types = {}

    def register_event_type(self, event_type_name, event_args):
        self._event_types[event_type_name] = EventType(event_type_name, event_args)
    
    def register_event_types(self, event_args, *event_type_names):
        for event_type_name in event_type_names:
            self.register_event_type(event_type_name, event_args)

    def reset(self, event_type_name=None):
        if event_type_name is None:
            for et in self._event_types.values():
                et.reset()
        else:
            self._call_event_type(event_type_name, lambda et: et.reset())

    def _call_event_type(self, event_type_name, callback):
        try:
            event_type = self._event_types[event_type_name]
        except KeyError:
            raise NoSuchEventType(event_type_name)
        callback(event_type)

    def subscribe_to_event_type(self, event_type_name, handler):
        self._call_event_type(event_type_name, lambda et: et.subscribe(handler))

    def subscribe_to_event_types(self, event_types):
        for event_type_name, handler in event_types.items():
            self.subscribe_to_event_type(event_type_name, handler)

    def unsubscribe_from_event_type(self, event_type_name, handler):
        self._call_event_type(event_type_name, lambda et: et.unsubscribe(handler))

    def fire(self, event_type_name, *args, **kwargs):
        self._call_event_type(event_type_name, lambda et: et.fire(*args, **kwargs))

    def add_listener(self, listener):
        for event_type_name in self._event_types.keys():
            try:
                sym = getattr(listener, event_type_name)
            except AttributeError:
                continue
            if not callable(sym):
                continue
            self.subscribe_to_event_type(event_type_name, sym)


eventmgr = EventManager()
register_event_type = eventmgr.register_event_type
register_event_types = eventmgr.register_event_types
subscribe_to_event_type = eventmgr.subscribe_to_event_type
subscribe_to_event_types = eventmgr.subscribe_to_event_types
unsubscribe_from_event_type = eventmgr.unsubscribe_from_event_type
add_listener = eventmgr.add_listener
reset = eventmgr.reset
fire = eventmgr.fire


###
# Global events
###

register_event_types(
    [Report],

    "on_tests_beginning", "on_tests_ending",
)

register_event_types(
    [],

    # test session setup & teardown beginning events
    "on_test_session_setup_beginning", "on_test_session_teardown_beginning"
)

register_event_types(
    [bool],

    # test session setup & teardown ending events
    "on_test_session_setup_ending", "on_test_session_teardown_ending",
)


###
# Suite events
###

register_event_types(
    [Suite],

    "on_suite_beginning", "on_suite_ending",
    "on_suite_setup_beginning",
    "on_suite_teardown_beginning"
)

register_event_types(
    [Suite, bool],

    "on_suite_setup_ending", "on_suite_teardown_ending"
)


###
# Test events
###

register_event_types(
    [Test],

    "on_test_beginning", "on_disabled_test",
    "on_test_setup_beginning", "on_test_teardown_beginning",
)

register_event_types(
    [Test, bool],

    "on_test_setup_ending", "on_test_teardown_ending"
)

register_event_type("on_skipped_test", [Test, str])
register_event_type("on_test_ending", [Test, str])


###
# Transverse test execution events
###

try:
    basestring
except NameError:
    # when using Python 3, just map basestring to str
    basestring = str

register_event_type("on_step", [basestring])
register_event_type("on_log", [str, basestring])
register_event_type("on_check", [basestring, bool, basestring])
register_event_type("on_log_attachment", [basestring, basestring])
register_event_type("on_log_url", [basestring, basestring])