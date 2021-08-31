import threading

from lemoncheesecake.helpers.threading import ThreadedFactory


def test_threaded_factory():
    class TestFactory(ThreadedFactory):
        def setup_object(self):
            return object()

    factory = TestFactory()
    objects = []

    class TestThread(threading.Thread):
        def run(self):
            objects.append(factory.get_object())
            objects.append(factory.get_object())

    thread_1 = TestThread()
    thread_1.start()
    thread_1.join()
    thread_2 = TestThread()
    thread_2.start()
    thread_2.join()

    assert len(objects) == 4
    assert objects[0] is objects[1]
    assert objects[2] is objects[3]
    assert objects[1] is not objects[2]


def test_threaded_factory_teardown():
    marker = []

    class TestFactory(ThreadedFactory):
        def setup_object(self):
            return 42

        def teardown_object(self, obj):
            marker.append(obj)

    factory = TestFactory()
    factory.get_object()
    factory.teardown_factory()

    assert marker == [42]
