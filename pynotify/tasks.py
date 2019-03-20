from celery import shared_task

from .helpers import process_task


@shared_task
def notification_task(*args, **kwargs):
    """
    Celery task used in asynchronous mode. Just passes any arguments to ``process_task`` function.
    """
    process_task(*args, **kwargs)
