import re

from chamber.models import SmartModel, SmartModelBase, SmartQuerySet
from django.conf import settings as django_settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.template import Context, Template
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l

from .config import settings
from .exceptions import MissingContextVariableError
from .helpers import DeletedRelatedObject, SecureRelatedObject, get_from_context, strip_html


TEMPLATE_FIELDS = ('title', 'text', 'trigger_action', 'extra_fields')


class BaseModel(SmartModel):
    """
    Base class for models that outpus its verbose name and PK.
    """
    def __str__(self):
        return '{} #{}'.format(self._meta.verbose_name, self.pk)

    def _clean_json_value(self, value):
        if value is not None and not isinstance(value, dict):
            raise ValidationError(_('Value must be a dictionary.'))

    class Meta:
        abstract = True


class BaseTemplate(BaseModel):
    """
    Base abstract model for notification template.

    Attributes:
        title: Title of the notification.
        text: Text of the notification.
        trigger_action: Arbitrary action performed when user triggers (i.e. clicks/taps) the notification.
        extra_fields: Can be used to store additional fields needed in particular use case.
    """
    title = models.CharField(max_length=200, verbose_name=_l('title'))
    text = models.TextField(null=True, blank=True, verbose_name=_l('text'))
    trigger_action = models.CharField(max_length=2500, null=True, blank=True,
                                      verbose_name=_l('trigger action'))
    extra_fields = models.JSONField(null=True, blank=True, encoder=DjangoJSONEncoder, verbose_name=_l('extra fields'))

    class Meta:
        abstract = True


class AdminNotificationTemplate(BaseTemplate):
    """
    Represents a "template of a template". This model is intended to be managed from administration, hence its name. It
    is identified by `slug`, which can be used for notification creation. However, this template is never used to
    directly render a notification, but instead is used to create `NotificationTemplate` with same values.

    Attributes:
        slug: Template slug, with which this template can be referred to.
        is_active: Flag that switches on/off creating notifications from this template.
        is_locked: Flag that switches on/off this template editing (for admin purposes, requires admin-side support).
        send_push: Flag that switches on/off sending push notifications from this template.
            Currently, it has no effect on its own, but you can use it in your custom push notification solution.
    """
    slug = models.SlugField(max_length=200, unique=True, verbose_name=_l('slug'))
    is_active = models.BooleanField(default=True, verbose_name=_l('is active'))
    is_locked = models.BooleanField(null=False, blank=False, default=False, verbose_name=_l('is locked'))
    send_push = models.BooleanField(default=False, verbose_name=_l('send push notification'))

    class Meta:
        verbose_name = _l('admin notification template')
        verbose_name_plural = _l('admin notification templates')

    def __str__(self):
        return '{} ({})'.format(super().__str__(), self.slug)


class NotificationTemplate(BaseTemplate):
    """
    Represents template that is used for rendering notification fields. Each field specified in ``TEMPLATE_FIELDS`` is a
    template string, that can be rendered using the ``render`` method.

    Attributes:
        admin_template: Reference to admin template that was used to create this notification template.
    """

    admin_template = models.ForeignKey(
        AdminNotificationTemplate,
        related_name="notification_templates",
        on_delete=models.SET_NULL,
        verbose_name=_l('admin notification template'),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _l('notification template')
        verbose_name_plural = _l('notification templates')
        # prevents duplicates in case of race condition (see BaseHandler._template)
        unique_together = TEMPLATE_FIELDS + ('admin_template',)

    @property
    def slug(self):
        return self.admin_template.slug if self.admin_template else None

    def _render_string(self, field, template_string, context):
        if settings.TEMPLATE_TRANSLATE:
            template_string = _(template_string)

        if settings.TEMPLATE_CHECK:
            vars = re.findall(r'{{ ?([^\|} ]+)[^}]*}}', template_string)
            for var in vars:
                value = get_from_context(var, context)
                if value is None or isinstance(value, DeletedRelatedObject):
                    raise MissingContextVariableError(field, var)

        output = Template('{}{}'.format(settings.TEMPLATE_PREFIX, template_string)).render(Context(context))

        if settings.STRIP_HTML:
            output = strip_html(output)

        return output

    def _render_dict(self, dictionary, context):
        rendered_dictionary = {}
        for key in dictionary:
            rendered_dictionary[key] = self._render_string(key, str(dictionary[key]), context)
        return rendered_dictionary

    def render(self, field, context):
        """
        Renders ``field`` using ``context``.
        """
        value = getattr(self, field)
        if isinstance(value, dict):
            return self._render_dict(value, context)
        else:
            return self._render_string(field, str(value), context) if value is not None else ''

    def clean_extra_fields(self):
        self._clean_json_value(self.extra_fields)


class NotificationQuerySet(SmartQuerySet):

    def _create_related_object(self, notification, obj, name=None):
        if not isinstance(obj, models.Model):
            raise TypeError('Related object must be an instance of model.')
        NotificationRelatedObject.objects.create(name=name, notification=notification, content_object=obj)

    def create(self, recipient, template, related_objects=None, **kwargs):
        notification = super().create(recipient=recipient, template=template, **kwargs)

        if related_objects is not None:
            if isinstance(related_objects, dict):
                for name, obj in related_objects.items():
                    self._create_related_object(notification, obj, name)
            elif isinstance(related_objects, list):
                for obj in related_objects:
                    self._create_related_object(notification, obj)
            else:
                raise TypeError('Related objects must be a list or dictionary in form {"name": object}.')

        return notification

    def filter_with_related_object(self, related_object):
        return self.filter(
            related_objects__content_type=ContentType.objects.get_for_model(related_object),
            related_objects__object_id=str(related_object.pk),
        )


class NotificationMeta(SmartModelBase, type):
    """
    Creates property for each template field. The property returns rendered template.
    """
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        for field in TEMPLATE_FIELDS:
            setattr(
                new_class,
                field,
                property(lambda self, field=field: self._render(field))
            )

        return new_class


class Notification(BaseModel, metaclass=NotificationMeta):
    """
    Represents the notification.

    Attributes specified in ``TEMPLATE_FIELDS`` are also available here, as generated properties,
    that are evaluated at runtime and will return rendered field from the associated template. By default, the context
    used for rendering is filled with named related objects and extra data, so they can be referenced in the template by
    their name/key.

    Attributes:
        recipient: Recipient of the notification.
        template: Template used to render generated notification fields.
        is_read: Boolean flag indicating that recipitent has seen the notification.
        is_triggered: Boolean flag indicating that recipient has triggered the notification (e.g. clicked/tapped)
        extra_data: JSON serialized dictionary with extra data.
    """
    recipient = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        related_name='notifications',
        on_delete=models.CASCADE,
        verbose_name=_l('recipient'),
    )
    template = models.ForeignKey(
        NotificationTemplate,
        related_name="notifications",
        on_delete=models.PROTECT,
        verbose_name=_l('template')
    )
    is_read = models.BooleanField(default=False, verbose_name=_l('is read'))
    is_triggered = models.BooleanField(default=False, verbose_name=_l('is triggered'))
    extra_data = models.JSONField(null=True, blank=True, encoder=DjangoJSONEncoder, verbose_name=_l('extra data'))

    objects = NotificationQuerySet.as_manager()

    class Meta:
        verbose_name = _l('notification')
        verbose_name_plural = _l('notifications')
        ordering = ('-created_at',)

    def _render(self, field):
        return self.template.render(field, self.context)

    def clean_extra_data(self):
        return self._clean_json_value(self.extra_data)

    def clean(self):
        keys = set(self.extra_data or {}) & set(obj.name for obj in self.related_objects.all() if obj.name)
        if keys:
            raise ValidationError('Related objects and extra data contain same key(s): {}'.format(', '.join(keys)))

    @cached_property
    def related_objects_dict(self):
        """
        Returns named related objects as a dictionary where key is name of the related object and value is the object
        itself. Related objects without name are skipped.
        """
        output = {}
        for obj in self.related_objects.filter(name__isnull=False):
            output[obj.name] = SecureRelatedObject(obj.content_object) if obj.content_object else DeletedRelatedObject()
        return output

    @property
    def context(self):
        """
        Returns context dictionary used for rendering the template.
        """
        return {**self.related_objects_dict, **(self.extra_data or {})}


class NotificationRelatedObject(BaseModel):
    """
    Represents object related to a notification. This object can be then referenced in notification template
    fields by its `name` (if not None).

    Attributes:
        name: String identificator of the object (for referencing in templates).
        notification: Related notification.
        content_object: The related object itself.
    """
    name = models.CharField(max_length=200, verbose_name=_l('name'), blank=True, null=True)
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='related_objects',
        verbose_name=_l('notification'),
    )
    content_type = models.ForeignKey(ContentType, null=True, on_delete=models.SET_NULL, verbose_name=_l('content type'))
    object_id = models.TextField(db_index=True, verbose_name=_l('object ID'))
    content_object = GenericForeignKey('content_type', 'object_id')
