from collections import Iterable

from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import cached_property

from .helpers import register
from .models import AdminNotificationTemplate, Notification, NotificationTemplate


class HandlerMeta(type):
    """
    Registers handler for handling of signal defined in handler's ``Meta``.
    """
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)

        # register only descendants of BaseHandler
        if bases:
            if not getattr(new_class, 'Meta', None):
                raise ImproperlyConfigured('{} must have Meta class defined.'.format(name))

            if getattr(new_class.Meta, 'abstract', False):
                # delete the abstract attribute so it is not inherited by child classes
                delattr(new_class.Meta, 'abstract')
            else:
                if not getattr(new_class, 'Meta', None) or not getattr(new_class.Meta, 'signal', None):
                    raise ImproperlyConfigured('No signal defined in {}\'s Meta.'.format(name))

                if (
                    getattr(new_class.Meta, 'allowed_senders', None)
                    and not isinstance(new_class.Meta.allowed_senders, Iterable)
                ):
                    raise ImproperlyConfigured('{}\'s attribute "allowed_senders" must be iterable.'.format(name))

                register(
                    signal=new_class.Meta.signal,
                    handler_class=new_class,
                    allowed_senders=getattr(new_class.Meta, 'allowed_senders', None),
                )

        return new_class


class BaseHandler(metaclass=HandlerMeta):
    """
    Base class for handling creation of notification(s). Its purpose is to process signal kwargs sent over a defined
    signal. There should be typically one handler (inherited from this class) for each signal. The handler must define
    inner class ``Meta`` with following supported attributes:

        * ``signal``: Signal to which handler will be registered
        * ``allowed_senders``: Handler will be called only if signal was sent by allowed sender
        * ``abstract``: If set to True, the handler will not be registered

    Attributes:
        dispatcher_classes: An iterable of dispatcher classes that will be used to dispatch each notification.
        template_slug: Slug of an existing admin template to be used. If not defined, you must define
            ``get_template_data()`` method.
    """
    dispatcher_classes = ()
    template_slug = None

    @cached_property
    def _admin_template(self):
        template_slug = self.get_template_slug()
        if template_slug:
            return AdminNotificationTemplate.objects.get(slug=template_slug)
        else:
            return None

    @cached_property
    def _template(self):
        if self._admin_template:
            template, _ = NotificationTemplate.objects.get_or_create(
                title=self._admin_template.title,
                text=self._admin_template.text,
                trigger_action=self._admin_template.trigger_action,
                admin_template=self._admin_template,
            )
        else:
            template, _ = NotificationTemplate.objects.get_or_create(**self.get_template_data())

        return template

    def _init_dispatchers(self):
        self.dispatchers = []
        for dispatcher_class in set(self.get_dispatcher_classes()):
            self.dispatchers.append(self._init_dispatcher(dispatcher_class))

    def _init_dispatcher(self, dispatcher_class):
        return dispatcher_class()

    def _can_create_notification(self, recipient):
        """
        Returns ``True`` if notification can be created for ``recipient``.
        """
        return True

    def _create_notification(self, recipient):
        """
        Creates notification for ``recipient``.
        """
        if self._can_create_notification(recipient):
            return Notification.objects.create(
                recipient=recipient,
                template=self._template,
                related_objects=self.get_related_objects(),
                extra_data=self.get_extra_data(),
            )

    def _can_dispatch_notification(self, notification, dispatcher):
        """
        Returns ``True`` if ``notification`` can be dispatched using ``dispatcher``.
        """
        return True

    def _dispatch_notification(self, notification, dispatcher):
        """
        Dispatches ``notification`` using ``dispatcher``.
        """
        if self._can_dispatch_notification(notification, dispatcher):
            dispatcher.dispatch(notification)

    def _can_handle(self):
        """
        Returns ``True`` if handler should handle creating of notification(s).
        """
        return not self._admin_template or self._admin_template.is_active

    def handle(self, signal_kwargs):
        """
        Handles creation of notifications from ``signal_kwargs``.
        """
        self.signal_kwargs = signal_kwargs
        if self._can_handle():
            self._init_dispatchers()
            for recipient in self.get_recipients():
                notification = self._create_notification(recipient)

                if notification:
                    for dispatcher in self.dispatchers:
                        self._dispatch_notification(notification, dispatcher)

    def get_recipients(self):
        """
        Returns an iterable of recipients for which notification will be created.
        """
        raise NotImplementedError()  # pragma: no cover

    def get_template_data(self):
        """
        Returns kwargs used to create a template. Not called if template slug is used.
        """
        raise NotImplementedError()  # pragma: no cover

    def get_related_objects(self):
        """
        Returns a list or dictionary of related objects in format {"name": object}. Named related objects (i.e. those
        passed using a dictionary) can be referred in notification template.
        """
        return None

    def get_extra_data(self):
        """
        Returns a dictionary with extra data, the values must be JSON serializable.
        """
        return None

    def get_template_slug(self):
        """
        Returns slug of an admin template to be used.
        """
        return self.template_slug

    def get_dispatcher_classes(self):
        """
        Returns iterable of dispatcher classes used to dispatch notification(s).
        """
        return self.dispatcher_classes
