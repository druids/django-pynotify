from django.test import TestCase, override_settings

from pynotify.config import settings


class ConfigTestCase(TestCase):

    def test_config_should_return_default_values(self):
        self.assertEqual(settings.RECEIVER, settings.DEFAULTS['RECEIVER'])

    @override_settings(PYNOTIFY_RECEIVER='abcd')
    def test_config_should_return_value_overriden_in_settings(self):
        self.assertEqual(settings.RECEIVER, 'abcd')

    def test_config_should_raise_exception_if_unknown_setting_is_accessed(self):
        with self.assertRaises(AttributeError):
            settings.BLAH_BLAH_BLAH
