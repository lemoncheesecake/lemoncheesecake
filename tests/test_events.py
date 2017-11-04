import time

import pytest

from lemoncheesecake.exceptions import MismatchingEventArguments
from lemoncheesecake import events

@pytest.fixture(autouse=True)
def reset_events():
    yield
    events.reset()


def test_subscribe_bad_handler_args():
    events.register_event_type("on_event", [str])
    with pytest.raises(MismatchingEventArguments):
        events.subscribe_to_event_type("on_event", lambda: 0)


def test_fire_without_argument():
    i_got_called = []
    def handler():
        i_got_called.append(1)
    events.register_event_type("on_event", [])
    events.subscribe_to_event_type("on_event", handler)
    events.fire("on_event")
    assert i_got_called


def test_fire_with_argument():
    i_got_called = []
    def handler(val):
        i_got_called.append(val)
    events.register_event_type("on_event", [int])
    events.subscribe_to_event_type("on_event", handler)
    events.fire("on_event", 42)
    assert i_got_called[0] == 42


def test_fire_with_event_time():
    now = time.time()
    i_got_called = []
    def handler(event_time):
        i_got_called.append(event_time)
    events.register_event_type("on_event", [])
    events.subscribe_to_event_type("on_event", handler)
    events.fire("on_event")
    assert i_got_called[0] >= now


def test_fire_bad_arguments_number():
    events.register_event_type("on_event", [])
    events.subscribe_to_event_type("on_event", lambda: 0)
    with pytest.raises(MismatchingEventArguments):
        events.fire("on_event", 42)


def test_fire_bad_argument_type():
    events.register_event_type("on_event", [str])
    events.subscribe_to_event_type("on_event", lambda s: 0)
    with pytest.raises(MismatchingEventArguments):
        events.fire("on_event", 42)


def test_unsubscribe():
    i_got_called = []
    def handler():
        i_got_called.append(1)
    events.register_event_type("on_event", [])
    events.subscribe_to_event_type("on_event", handler)
    events.unsubscribe_from_event_type("on_event", handler)
    events.fire("on_event")
    assert len(i_got_called) == 0


def test_reset():
    i_got_called = []
    def handler():
        i_got_called.append(1)
    events.register_event_type("on_event", [])
    events.subscribe_to_event_type("on_event", handler)
    events.reset()
    events.fire("on_event")
    assert len(i_got_called) == 0
