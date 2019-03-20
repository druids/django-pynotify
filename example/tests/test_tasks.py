from unittest.mock import patch

from django.test import TestCase

from pynotify.tasks import notification_task


class TaskTestCase(TestCase):

    def test_notification_task_should_pass_all_arguments_to_process_task_function(self):
        with patch('pynotify.tasks.process_task') as mock:
            notification_task('abc', 'def')
            mock.assert_called_once_with('abc', 'def')
            mock.reset_mock()

            notification_task(abc=123, efg=456)
            mock.assert_called_once_with(abc=123, efg=456)
