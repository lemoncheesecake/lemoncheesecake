from __future__ import absolute_import
from typing import Any
import threading


class ThreadedFactory:
    """
    .. versionadded:: 1.9.0

    This factory class returns a new object per thread when calling :py:func:`get_object`.

    This class works by subclassing and:

    - implementing the :py:func:`setup_object` is MANDATORY
    - implementing the :py:func:`teardown_object` is optional

    NB: if the ``__init__`` method is overridden then the base class ``__init__`` method
    must be called.
    """

    def __init__(self) -> None:
        self._local = threading.local()
        self._objects = []

    def get_object(self) -> Any:
        """
        Get the object, it will be only created once per thread.
        """
        try:
            return self._local.object
        except AttributeError:
            obj = self.setup_object()
            self._local.object = obj
            self._objects.append(obj)
            return obj

    def teardown_factory(self) -> None:
        """
        Teardown the factory.

        This method must be called if :py:func:`teardown_object` has been implemented.
        """
        for obj in self._objects:
            self.teardown_object(obj)

    def setup_object(self) -> Any:
        """
        Create the object. This method MUST be implemented.
        """
        raise NotImplementedError()

    def teardown_object(self, obj: Any) -> None:
        """
        Teardown an object. You can implement this method if your object needs a special teardown phase.

        :param obj: an object created by :py:func:`setup_object`
        """
        pass
