from importlib import import_module
import logging
from pydoc import locate

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext as _

from .config import settings


logger = logging.getLogger(__name__)


class SecureRelatedObject:
    """
    Security proxy class allowing to access only string representation of the related object and a set of attributes
    defined in `RELATED_OBJECTS_ALLOWED_ATTRS` settings.
    """
    def __init__(self, related_object):
        self._object = related_object

    def __getattr__(self, name):
        if name in settings.RELATED_OBJECTS_ALLOWED_ATTRIBUTES:
            return getattr(self._object, name)
        else:
            raise AttributeError('Attribute "{}" is not allowed to be accessed on related object.'.format(name))

    def __str__(self):
        return self._object.__str__()


class DeletedRelatedObject:
    """
    Placeholder class that substitutes deleted related object and returns:
        * "[DELETED]" as its string representation
        * itself for any attribute accessed
    """
    def __getattr__(self, name):
        return self

    def __str__(self):
        return _('[DELETED]')


class SignalMap:
    """
    Maps signals to arbitrary values.
    """
    def __init__(self):
        self.map = {}

    def add(self, signal, value):
        if signal not in self.map:
            self.map[signal] = [value]
        else:
            self.map[signal].append(value)

    def get(self, signal):
        return self.map.get(signal, [])

    def remove(self, signal):
        if signal in self.map:
            del self.map[signal]


signal_map = SignalMap()


def register(signal, handler_class, allowed_senders=None):
    """
    Starts listening to ``signal`` and registers ``handler_class`` to it.
    """
    signal_map.add(signal, (handler_class, allowed_senders))
    signal.connect(receive, dispatch_uid='pynotify')


def receive(sender, **kwargs):
    """
    Initiates processing of the signal by notification handlers through a receiver.
    """
    if not settings.ENABLED:
        return

    signal = kwargs.pop('signal')
    receiver_class = locate(settings.RECEIVER)

    if not receiver_class:
        raise ImproperlyConfigured('Unable to locate receiver class {}'.format(settings.RECEIVER))

    for handler_class, allowed_senders in signal_map.get(signal):
        if allowed_senders and sender not in allowed_senders:
            continue
        receiver_class(handler_class).receive(kwargs)


def autoload():
    """
    Attempts to load (import) notification handlers from apps defined in ``PYNOTIFY_AUTOLOAD_APPS``
    """
    apps = settings.AUTOLOAD_APPS
    if apps:
        for app in apps:
            try:
                import_module('{}.handlers'.format(app))
            except ImportError:
                logger.exception('Failed to autoload notification handlers from app {}'.format(app))


def process_task(handler_class, serializer_class, signal_kwargs):
    """
    Deserializes signal kwargs using the given serializer and calls given handler.  This function is intended to be
    called from a Celery task.
    """
    handler_class = locate(handler_class)
    serializer_class = locate(serializer_class)
    signal_kwargs = serializer_class().deserialize(signal_kwargs)

    handler_class().handle(signal_kwargs)


def get_import_path(_class):
    """
    Returns import path for a given class.
    """
    return '{}.{}'.format(_class.__module__, _class.__name__)
