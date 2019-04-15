from unittest.mock import MagicMock

from django.contrib.auth.models import User
from django.test import TestCase

from pynotify.models import NotificationTemplate
from pynotify.notify import notify


class MockDispatcher:
    dispatch = MagicMock()


class NotifyTestCase(TestCase):

    def setUp(self):
        self.template = NotificationTemplate.objects.create(title='Hi!', slug='my-template')
        self.user = User.objects.create_user('John')

    def test_notify_should_create_notification(self):
        notify(
            recipients=[self.user],
            title='{{greeting}} {{user}}!',
            text='Welcome to PyNotify!',
            trigger_action='http://localhost/',
            related_objects={'user': self.user},
            extra_data={'greeting': 'Hello'},
            dispatcher_classes=(MockDispatcher,)
        )

        notification = self.user.notifications.get()

        self.assertEqual(notification.title, 'Hello John!')
        self.assertEqual(notification.text, 'Welcome to PyNotify!')
        self.assertEqual(notification.trigger_action, 'http://localhost/')
        MockDispatcher.dispatch.assert_called_once_with(notification)

    def test_notify_should_create_notification_from_existing_template(self):
        notify(
            recipients=[self.user],
            template_slug='my-template'
        )

        notification = self.user.notifications.get()
        self.assertEqual(notification.title, 'Hi!')

    def test_notify_should_accept_either_template_data_or_template_slug(self):
        with self.assertRaises(ValueError):
            notify(
                recipients=[self.user],
                title='Greetings!',
                template_slug='my-template',
            )

        with self.assertRaises(ValueError):
            notify(recipients=[self.user])
