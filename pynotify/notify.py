from django.dispatch import Signal

from .handlers import BaseHandler


notify_signal = Signal(providing_args=['recipients', 'title', 'text', 'trigger_action', 'related_objects'])


def notify(recipients, title, text=None, trigger_action=None, related_objects=None):
    """
    Helper method to create a notification. Simply sends the ``notify_signal``.
    """
    notify_signal.send(
        sender=None,
        recipients=recipients,
        title=title,
        text=text,
        trigger_action=trigger_action,
        related_objects=related_objects
    )


class NotifyHandler(BaseHandler):
    """
    Notification handler for ``notify_signal``.
    """
    def get_recipients(self):
        return self.signal_kwargs['recipients']

    def get_template_data(self):
        return {x: self.signal_kwargs[x] for x in {'title', 'text', 'trigger_action'}}

    def get_related_objects(self):
        return self.signal_kwargs['related_objects']

    class Meta:
        signal = notify_signal
