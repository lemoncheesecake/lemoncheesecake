import time

from lemoncheesecake.utils import get_callable_args
from lemoncheesecake.exceptions import NoSuchEventType, MismatchingEventArguments
from lemoncheesecake.suite import Suite, Test
from lemoncheesecake.reporting import Report


class EventType:
    def __init__(self, event_arg_types):
        self._event_arg_types = event_arg_types
        self._handlers = []

    def _has_extra_time_arg(self, args):
        return (len(args) == len(self._event_arg_types) + 1) and args[-1].endswith("_time")

    def subscribe(self, handler):
        handler_args = get_callable_args(handler)

        handler_args_number = len(handler_args) - (1 if self._has_extra_time_arg(handler_args) else 0)
        if handler_args_number != len(self._event_arg_types):
            raise MismatchingEventArguments("Expecting %d arguments, got %d (not counting possible extra event_time argument)" % (
                len(self._event_arg_types), handler_args_number
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

    def fire(self, *args):
        event_time = time.time()

        if len(args) != len(self._event_arg_types):
            raise MismatchingEventArguments("Expecting %d arguments, got %d" % (
                len(self._event_arg_types), len(args)
            ))

        i = 0
        for handler_arg, event_arg in zip(args, self._event_arg_types):
            if type(handler_arg) != event_arg:
                raise MismatchingEventArguments("Expecting type '%s' for argument #%d, got '%s'" % (
                    event_arg, i+1, type(handler_arg)
                ))
            i += 1

        for handler in self._handlers:
            self._handle_event(handler, args, event_time)


class EventManager:
    def __init__(self):
        self._event_types = {}

    def register_event_type(self, event_type_name, event_args):
        self._event_types[event_type_name] = EventType(event_args)
    
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

    def subscribe(self, event_type_name, handler):
        self._call_event_type(event_type_name, lambda et: et.subscribe(handler))

    def unsubscribe(self, event_type_name, handler):
        self._call_event_type(event_type_name, lambda et: et.unsubscribe(handler))

    def fire(self, event_type_name, *args):
        self._call_event_type(event_type_name, lambda et: et.fire(*args))


eventmgr = EventManager()
register_event_type = eventmgr.register_event_type
register_event_types = eventmgr.register_event_types
subscribe = eventmgr.subscribe
unsubscribe = eventmgr.unsubscribe
reset = eventmgr.reset
fire = eventmgr.fire


###
# Global events
###

register_event_types(
    [],

    # test session setup & teardown events
    "on_tests_beginning", "on_tests_ending"

    # (whole) tests beginning & ending events
    "on_test_session_setup_beginning", "on_test_session_setup_ending",
    "on_test_session_teardown_beginning", "on_test_session_teardown_ending"
)


###
# Suite events
###

register_event_types(
    [Suite],

    "on_suite_beginning", "on_suite_ending",
    "on_suite_setup_beginning", "on_suite_setup_ending",
    "on_suite_teardown_beginning", "on_suite_teardown_ending"
)


###
# Test events
###

register_event_types(
    [Test],

    "on_test_beginning", "on_test_ending",
    "on_test_setup_beginning", "on_test_setup_ending",
    "on_test_teardown_beginning", "on_test_teardown_ending"
)

register_event_type("on_skipped_test", [Test, str])


###
# Transverse test execution events
###

register_event_type("on_step", [str])
register_event_type("on_log", [str, str])
register_event_type("on_check", [str, bool, str])


###
# Reporting events
###

register_event_types(
    [Report],

    "on_report_creation", "on_report_ending"
)
