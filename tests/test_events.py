from lemoncheesecake.events import EventManager, Event


def process_events(eventmgr):
    eventmgr.end_of_events()
    eventmgr.handler_loop()


class MyEvent(Event):
    def __init__(self, val):
        super(MyEvent, self).__init__()
        self.val = val


def test_fire():
    i_got_called = []
    def handler(event):
        i_got_called.append(event.val)
    eventmgr = EventManager()
    eventmgr.register_event(MyEvent)
    eventmgr.subscribe_to_event(MyEvent, handler)
    eventmgr.fire(MyEvent(42))
    process_events(eventmgr)
    assert i_got_called[0] == 42


def test_unsubscribe():
    i_got_called = []
    def handler(event):
        i_got_called.append(event.val)
    eventmgr = EventManager()
    eventmgr.register_event(MyEvent)
    eventmgr.subscribe_to_event(MyEvent, handler)
    eventmgr.unsubscribe_from_event(MyEvent, handler)
    eventmgr.fire(MyEvent(42))
    process_events(eventmgr)
    assert len(i_got_called) == 0


def test_reset():
    i_got_called = []
    def handler(event):
        i_got_called.append(event.val)
    eventmgr = EventManager()
    eventmgr.register_event(MyEvent)
    eventmgr.subscribe_to_event(MyEvent, handler)
    eventmgr.reset()
    eventmgr.fire(MyEvent(42))
    process_events(eventmgr)
    assert len(i_got_called) == 0
