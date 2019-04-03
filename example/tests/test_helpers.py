from unittest.mock import MagicMock, patch

from django.core.exceptions import ImproperlyConfigured
from django.dispatch import Signal
from django.test import TestCase, override_settings

from pynotify.helpers import autoload, get_import_path, process_task, register, signal_map

from .test_app.signals import autoload_signal


# MOCK OBJECTS ------------------------------------------------------------------------------------


test_signal = Signal(providing_args=['abc'])


class MockHandler1(MagicMock):

    signal_kwargs = None

    def __init__(self):
        MockHandler1.signal_kwargs = None

    def handle(self, signal_kwargs):
        MockHandler1.signal_kwargs = signal_kwargs


class MockHandler2(MagicMock):
    pass


class MockSerializer(MagicMock):
    deserialize = MagicMock(side_effect=lambda value: value)


# TESTS -------------------------------------------------------------------------------------------


class HelpersTestCase(TestCase):

    def tearDown(self):
        signal_map.remove(test_signal)

    def test_signal_map_should_return_empty_list_for_unknown_signal(self):
        self.assertEqual(signal_map.get(test_signal), [])

    def test_signal_map_should_return_list_values_for_known_signal(self):
        signal_map.add(test_signal, MockHandler1)
        self.assertEqual(signal_map.get(test_signal), [MockHandler1])
        signal_map.add(test_signal, MockHandler2)
        self.assertEqual(signal_map.get(test_signal), [MockHandler1, MockHandler2])

    def test_register_should_add_handler_class_and_allowed_senders_to_signal_map(self):
        register(test_signal, MockHandler1, self.__class__)
        self.assertEqual(signal_map.get(test_signal), [(MockHandler1, self.__class__)])

    def test_register_should_connect_receive_function_to_the_signal(self):
        register(test_signal, MockHandler1)
        # not very clever test, but patching here is problematic
        self.assertEqual(test_signal.receivers[0][0][0], 'pynotify')

    @override_settings(PYNOTIFY_RECEIVER='abc123')
    def test_receive_should_fail_if_receiver_is_misconfigured(self):
        register(test_signal, MockHandler1)
        with self.assertRaises(ImproperlyConfigured):
            test_signal.send(sender='abc', abc=123)

    @override_settings(PYNOTIFY_RECEIVER='pynotify.receivers.SynchronousReceiver')
    def test_receive_should_pass_signal_kwargs_to_handler_through_receiver(self):
        register(test_signal, MockHandler1)
        test_signal.send(sender='abc', abc=123)
        self.assertEqual(MockHandler1.signal_kwargs, {'abc': 123})

    @override_settings(PYNOTIFY_ENABLED=False)
    def test_receive_should_not_call_handler_if_pynotify_not_enabled(self):
        MockHandler1.signal_kwargs = 'constant'
        register(test_signal, MockHandler1)
        test_signal.send(sender='abc', abc=123)
        self.assertEqual(MockHandler1.signal_kwargs, 'constant')

    @override_settings(PYNOTIFY_RECEIVER='pynotify.receivers.SynchronousReceiver')
    def test_receive_should_not_call_handler_if_disallowed_sender_sent_the_signal(self):
        MockHandler1.signal_kwargs = 'constant'
        register(test_signal, MockHandler1, allowed_senders='abc')
        test_signal.send(sender='def', abc=123)
        self.assertEqual(MockHandler1.signal_kwargs, 'constant')

    def test_process_task_should_call_handler(self):
        process_task(
            handler_class=get_import_path(MockHandler1),
            serializer_class=get_import_path(MockSerializer),
            signal_kwargs={'abc': 1234}
        )
        MockSerializer.deserialize.assert_called_once_with({'abc': 1234})
        self.assertEqual(MockHandler1.signal_kwargs, {'abc': 1234})

    def test_get_import_path_should_return_import_path_of_the_class(self):
        self.assertEqual(get_import_path(MockHandler1), 'example.tests.test_helpers.MockHandler1')

    @override_settings(PYNOTIFY_AUTOLOAD_APPS=('example.tests.test_app',))
    def test_handlers_should_be_autoloaded_from_specified_apps(self):
        self.assertEqual(signal_map.get(autoload_signal), [])
        autoload()

        handler, _ = signal_map.get(autoload_signal)[0]

        from .test_app.handlers import AutoloadHandler
        self.assertEqual(handler, AutoloadHandler)
        signal_map.remove(autoload_signal)

    @override_settings(PYNOTIFY_AUTOLOAD_APPS=('example.tests.test_app2',))
    def test_if_autoload_fails_it_should_be_logged(self):
        with patch('pynotify.helpers.logger') as logger:
            autoload()
            self.assertEqual(signal_map.get(autoload_signal), [])
            logger.exception.assert_called_once()
