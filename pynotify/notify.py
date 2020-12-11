from django.dispatch import Signal

from .handlers import BaseHandler


notify_signal = Signal(providing_args=['recipients', 'title', 'text', 'trigger_action', 'related_objects',
                                       'extra_data', 'template_slug', 'dispatcher_classes'])


def notify(recipients, title=None, text=None, trigger_action=None, related_objects=None, extra_data=None,
           template_slug=None, dispatcher_classes=None):
    """
    Helper method to create a notification. Simply sends the ``notify_signal``.
    """
    if bool(template_slug) == (bool(title) | bool(text) | bool(trigger_action)):
        raise ValueError('Either provide template slug or template data, not both.')

    notify_signal.send(
        sender=None,
        recipients=recipients,
        title=title,
        text=text,
        trigger_action=trigger_action,
        related_objects=related_objects,
        extra_data=extra_data,
        template_slug=template_slug,
        dispatcher_classes=dispatcher_classes,
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

    def get_extra_data(self):
        return self.signal_kwargs['extra_data']

    def get_template_slug(self):
        return self.signal_kwargs['template_slug']

    def get_dispatcher_classes(self):
        return self.signal_kwargs['dispatcher_classes'] or ()

    class Meta:
        signal = notify_signal
