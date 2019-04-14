from lemoncheesecake.events import AsyncEventManager, SyncEventManager, Event


class MyEvent(Event):
    def __init__(self, val):
        super(MyEvent, self).__init__()
        self.val = val


def test_async_fire():
    i_got_called = []
    def handler(event):
        i_got_called.append(event.val)
    eventmgr = AsyncEventManager()
    eventmgr.register_event(MyEvent)
    eventmgr.subscribe_to_event(MyEvent, handler)
    with eventmgr.handle_events():
        eventmgr.fire(MyEvent(42))
    assert i_got_called


def test_sync_fire():
    i_got_called = []
    def handler(event):
        i_got_called.append(event.val)
    eventmgr = SyncEventManager()
    eventmgr.register_event(MyEvent)
    eventmgr.subscribe_to_event(MyEvent, handler)
    eventmgr.fire(MyEvent(42))
    assert i_got_called


def test_unsubscribe():
    i_got_called = []
    def handler(event):
        i_got_called.append(event.val)
    eventmgr = AsyncEventManager()
    eventmgr.register_event(MyEvent)
    eventmgr.subscribe_to_event(MyEvent, handler)
    eventmgr.unsubscribe_from_event(MyEvent, handler)
    with eventmgr.handle_events():
        eventmgr.fire(MyEvent(42))
    assert not i_got_called
