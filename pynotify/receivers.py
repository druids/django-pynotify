from pydoc import locate

from django.core.exceptions import ImproperlyConfigured
from django.db.transaction import on_commit

from .config import settings
from .helpers import get_import_path
from .serializers import ModelSerializer


class BaseReceiver:
    """
    Base class for receiving signals. Its purpose is to pass signal kwargs to the notification handler.
    """
    def __init__(self, handler_class):
        self.handler_class = handler_class

    def receive(self, signal_kwargs):
        """
        This method should implement passing ``signal_kwargs`` to the handler.
        """
        raise NotImplementedError()  # pragma: no cover


class SynchronousReceiver(BaseReceiver):
    """
    Signal receiver that calls notification handler synchronously.
    """
    def __init__(self, handler_class):
        super().__init__(handler_class)
        self.handler = self.handler_class()

    def receive(self, signal_kwargs):
        self.handler.handle(signal_kwargs)


class AsynchronousReceiver(BaseReceiver):
    """
    Signal receiver that calls notification handler asynchronously via Celery.
    """
    def __init__(self, handler_class):
        super().__init__(handler_class)
        self.serializer_class = ModelSerializer
        self.celery_task = self._get_celery_task()

    def _get_celery_task(self):
        celery_task = settings.CELERY_TASK
        if not celery_task:
            raise ImproperlyConfigured(
                'CELERY_TASK setting must be set when using {}.'.format(self.__class__.__name__)
             )
        return locate(celery_task)

    def receive(self, signal_kwargs):
        # Call of the Celery task should be performed after current DB transaction is commited to avoid race condition,
        # e.g. accessing referenced object in the task before it has finished saving into DB.
        on_commit(lambda: self.celery_task.delay(
            get_import_path(self.handler_class),
            get_import_path(self.serializer_class),
            self.serializer_class().serialize(signal_kwargs),
        ))
