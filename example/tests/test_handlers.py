from copy import copy
from unittest.mock import MagicMock

from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.dispatch import Signal
from django.test import TestCase

from pynotify.dispatchers import BaseDispatcher
from pynotify.handlers import BaseHandler
from pynotify.helpers import signal_map
from pynotify.models import AdminNotificationTemplate


# MOCK OBJECTS ------------------------------------------------------------------------------------


test_signal_data = Signal(providing_args=['recipients'])
test_signal_slug = Signal(providing_args=['recipients'])


class MockNotification:
    objects = MagicMock()


class MockSender:
    pass


class MockDispatcher(BaseDispatcher):

    dispatched_notifications = []

    def __init__(self, *args, **kwargs):
        MockDispatcher.dispatched_notifications = []

    def dispatch(self, notification):
        MockDispatcher.dispatched_notifications.append(notification)


class TestDataHandler(BaseHandler):

    # two identical dispatcher classes are intentional, duplicates must be ignored
    dispatcher_classes = (MockDispatcher, MockDispatcher)

    def get_recipients(self):
        return self.signal_kwargs['recipients']

    def get_template_data(self):
        return {'title': 'Hello data!'}

    def get_related_objects(self):
        return {'first_recipient': self.signal_kwargs['recipients'][0]}

    def get_extra_data(self):
        return {'some_value': 123}

    def _can_create_notification(self, recipient):
        return recipient.username != 'James'

    def _can_dispatch_notification(self, notification, dispatcher):
        return notification.recipient.username != 'John'

    def _can_handle(self):
        return super()._can_handle() and self.signal_kwargs.get('can_handle', True)

    class Meta:
        signal = test_signal_data


class TestSlugHandler(BaseHandler):

    template_slug = 'test_slug'

    def get_recipients(self):
        return self.signal_kwargs['recipients']

    class Meta:
        signal = test_signal_slug
        allowed_senders = (MockSender,)


# TESTS -------------------------------------------------------------------------------------------


class HandlerTestCase(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user('Jack')
        self.user2 = User.objects.create_user('John')
        self.user3 = User.objects.create_user('James')
        self.template = AdminNotificationTemplate.objects.create(title='Hello slug!', slug='test_slug')

    def test_handler_should_be_automatically_registered(self):
        self.assertEqual(signal_map.get(test_signal_data), [(TestDataHandler, None)])
        self.assertEqual(signal_map.get(test_signal_slug), [(TestSlugHandler, (MockSender,))])

    def test_handler_should_not_be_automatically_registered_if_meta_is_not_defined(self):
        with self.assertRaises(ImproperlyConfigured):
            class TestHandler(BaseHandler):
                pass

    def test_handler_should_not_be_automatically_registered_if_signal_is_not_defined(self):
        with self.assertRaises(ImproperlyConfigured):
            class TestHandler(BaseHandler):
                class Meta:
                    pass

    def test_handler_should_not_be_automatically_registered_if_allowed_senders_is_not_iterable(self):
        with self.assertRaises(ImproperlyConfigured):
            class TestHandler(BaseHandler):
                class Meta:
                    signal = test_signal_data
                    allowed_senders = 123

    def test_handler_should_not_be_automatically_registered_if_it_is_abstract(self):
        map = copy(signal_map.map)

        class TestHandler(BaseHandler):
            class Meta:
                abstract = True

        self.assertEqual(signal_map.map, map)

    def test_handler_should_create_notification_using_template_data(self):
        users = [self.user1, self.user2]
        test_signal_data.send(sender=None, recipients=[self.user1, self.user2, self.user3])

        for user in users:
            notification = user.notifications.get()
            related_object = notification.related_objects.get()

            self.assertEqual(notification.recipient, user)
            self.assertEqual(notification.title, 'Hello data!')
            self.assertEqual(notification.get_extra_data(), {'some_value': 123})
            self.assertEqual(related_object.name, 'first_recipient')
            self.assertEqual(related_object.content_object, self.user1)
            if user.username == 'Jack':
                self.assertIn(notification, MockDispatcher.dispatched_notifications)

        self.assertEqual(len(MockDispatcher.dispatched_notifications), 1)

        # Repeated notification should use the same template
        test_signal_data.send(sender=None, recipients=[self.user1])
        notifications = self.user1.notifications.all()
        self.assertEqual(notifications[0].template, notifications[1].template)

        # Test _can_handle() method is used
        self.user1.notifications.all().delete()
        test_signal_data.send(sender=None, recipients=[self.user1], can_handle=False)
        self.assertEqual(self.user1.notifications.count(), 0)

    def test_handler_should_create_notification_using_template_slug(self):
        test_signal_slug.send(sender=MockSender, recipients=[self.user1])
        notification = self.user1.notifications.get()
        self.assertEqual(notification.template.admin_template, self.template)
        self.assertEqual(notification.title, 'Hello slug!')

    def test_handler_should_respect_is_active_flag_of_admin_template(self):
        # inactive admin template
        self.template.change_and_save(is_active=False)
        test_signal_slug.send(sender=MockSender, recipients=[self.user1])
        self.assertEqual(self.user1.notifications.all().count(), 0)

        # active admin template
        self.template.change_and_save(is_active=True)
        test_signal_slug.send(sender=MockSender, recipients=[self.user1])
        self.assertEqual(self.user1.notifications.all().count(), 1)
