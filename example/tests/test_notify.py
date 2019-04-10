from django.contrib.auth.models import User
from django.test import TestCase

from pynotify.notify import notify


class NotifyTestCase(TestCase):

    def test_notify_should_create_notification(self):
        user = User.objects.create_user('John')
        notify(
            recipients=[user],
            title='{{greeting}} {{user}}!',
            text='Welcome to PyNotify!',
            trigger_action='http://localhost/',
            related_objects={'user': user},
            extra_data={'greeting': 'Hello'},
        )

        notification = user.notifications.get()

        self.assertEqual(notification.title, 'Hello John!')
        self.assertEqual(notification.text, 'Welcome to PyNotify!')
        self.assertEqual(notification.trigger_action, 'http://localhost/')
