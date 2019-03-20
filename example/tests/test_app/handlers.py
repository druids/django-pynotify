from pynotify.handlers import BaseHandler

from .signals import autoload_signal


class AutoloadHandler(BaseHandler):

    class Meta:
        signal = autoload_signal
