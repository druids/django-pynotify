from unittest.mock import MagicMock

from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.db.transaction import commit
from django.test import TestCase, TransactionTestCase, override_settings

from pynotify.receivers import AsynchronousReceiver, SynchronousReceiver


# MOCK OBJECTS ------------------------------------------------------------------------------------


mock_task = MagicMock()


class ReceiverTestMixin:

    def setUp(self):
        self.signal_kwargs = {
            'user': User.objects.create_user('John'),
            'score': 123,
        }


# TESTS --------------------------------------------------------------------------------------------


class SynchronousReceiverTestCase(ReceiverTestMixin, TestCase):

    def test_receiver_should_pass_signal_kwargs_to_handler(self):
        receiver = SynchronousReceiver(MagicMock)
        receiver.receive(self.signal_kwargs)
        receiver.handler.handle.assert_called_once_with(self.signal_kwargs)


class AsynchronousReceiverTestCase(ReceiverTestMixin, TransactionTestCase):

    @override_settings(PYNOTIFY_CELERY_TASK=None)
    def test_receiver_should_not_initalize_without_celery_task_setting(self):
        with self.assertRaises(ImproperlyConfigured):
            AsynchronousReceiver(MagicMock)

    @override_settings(PYNOTIFY_CELERY_TASK='tests.test_receivers.mock_task')
    def test_receiver_should_pass_serialized_kwargs_to_celery_task(self):
        receiver = AsynchronousReceiver(MagicMock)
        receiver.receive(self.signal_kwargs)
        commit()

        receiver.celery_task.delay.assert_called_with(
            handler_class='unittest.mock.MagicMock',
            serializer_class='pynotify.serializers.ModelSerializer',
            signal_kwargs=receiver.serializer_class().serialize(self.signal_kwargs),
        )

    @override_settings(PYNOTIFY_CELERY_TASK='tests.test_receivers.mock_task')
    def test_receiver_should_allow_overriding_of_celery_task_kwargs(self):
        receiver = AsynchronousReceiver(MagicMock)
        receiver._get_celery_task_kwargs = MagicMock(return_value={'abc': 1})
        receiver.receive(self.signal_kwargs)
        commit()
        receiver.celery_task.delay.assert_called_with(abc=1)
