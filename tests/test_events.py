import pytest

from lemoncheesecake import events


@pytest.fixture(autouse=True)
def reset_events():
    yield
    events.reset()


def process_events():
    events.end_of_events()
    events.handler_loop()


class MyEvent(events.Event):
    def __init__(self, val):
        super(MyEvent, self).__init__()
        self.val = val


def test_fire():
    i_got_called = []
    def handler(event):
        i_got_called.append(event.val)
    events.register_event(MyEvent)
    events.subscribe_to_event(MyEvent, handler)
    events.fire(MyEvent(42))
    process_events()
    assert i_got_called[0] == 42


def test_unsubscribe():
    i_got_called = []
    def handler(event):
        i_got_called.append(event.val)
    events.register_event(MyEvent)
    events.subscribe_to_event(MyEvent, handler)
    events.unsubscribe_from_event(MyEvent, handler)
    events.fire(MyEvent(42))
    process_events()
    assert len(i_got_called) == 0


def test_reset():
    i_got_called = []
    def handler(event):
        i_got_called.append(event.val)
    events.register_event(MyEvent)
    events.subscribe_to_event(MyEvent, handler)
    events.reset()
    events.fire(MyEvent(42))
    process_events()
    assert len(i_got_called) == 0
