from django.apps import AppConfig

from .helpers import autoload


class PyNotifyConfig(AppConfig):
    name = 'pynotify'
    verbose_name = 'PyNotify'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        from .notify import NotifyHandler  # noqa
        autoload()
