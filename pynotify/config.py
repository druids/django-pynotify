from django.conf import settings as django_settings


class Settings:
    """
    Holds default configuration values, the values can be overriden in settings with ``PYNOTIFY_`` prefix.
    """
    PREFIX = 'PYNOTIFY'
    DEFAULTS = {
        'AUTOLOAD_APPS': None,
        'CELERY_TASK': 'pynotify.tasks.notification_task',
        'RECEIVER': 'pynotify.receivers.SynchronousReceiver',
        'TEMPLATE_CHECK': False,
        'TEMPLATE_TRANSLATE': False,
    }

    def __getattr__(self, attr):
        if attr not in self.DEFAULTS:
            raise AttributeError('Invalid setting: "{}"').format(attr)

        return getattr(django_settings, '{}_{}'.format(self.PREFIX, attr), self.DEFAULTS[attr])


settings = Settings()
