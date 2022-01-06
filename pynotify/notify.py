from django.dispatch import Signal

from .handlers import BaseHandler
from .models import NotificationTemplate


notify_signal = Signal(providing_args=('recipients', 'related_objects', 'extra_data', 'template_slug',
                                       'dispatcher_classes') + NotificationTemplate.TEMPLATE_FIELDS)


def notify(recipients, related_objects=None, extra_data=None, template_slug=None, dispatcher_classes=None,
           **template_fields):
    """
    Helper method to create a notification. Simply sends the ``notify_signal``.
    """
    if bool(template_slug) == any(template_fields.values()):
        raise ValueError('Either provide template slug or template data, not both.')

    notify_signal.send(
        sender=None,
        recipients=recipients,
        related_objects=related_objects,
        extra_data=extra_data,
        template_slug=template_slug,
        dispatcher_classes=dispatcher_classes,
        **template_fields,
    )


class NotifyHandler(BaseHandler):
    """
    Notification handler for ``notify_signal``.
    """
    def get_recipients(self):
        return self.signal_kwargs['recipients']

    def get_template_data(self):
        return {x: self.signal_kwargs.get(x) for x in NotificationTemplate.TEMPLATE_FIELDS}

    def get_related_objects(self):
        return self.signal_kwargs['related_objects']

    def get_extra_data(self):
        return self.signal_kwargs['extra_data']

    def get_template_slug(self):
        return self.signal_kwargs['template_slug']

    def get_dispatcher_classes(self):
        return self.signal_kwargs['dispatcher_classes'] or ()

    class Meta:
        signal = notify_signal
