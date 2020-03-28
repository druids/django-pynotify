import json
import re

from chamber.models import SmartModel, SmartModelBase
from django.conf import settings as django_settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.template.base import Context, Template
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l

from .config import settings
from .exceptions import MissingContextVariableError
from .helpers import DeletedRelatedObject, SecureRelatedObject


class BaseModel(SmartModel):
    """
    Base class for models that outpus its verbose name and PK.
    """
    def __str__(self):
        return '{} #{}'.format(self._meta.verbose_name, self.pk)

    class Meta:
        abstract = True


class BaseTemplate(BaseModel):
    """
    Base abstract model for notification template.

    Attributes:
        title: Title of the notification.
        text: Text of the notification.
        trigger_action: Arbitrary action performed when user triggers (i.e. clicks/taps) the notification.
    """
    title = models.CharField(max_length=200, verbose_name=_l('title'))
    text = models.TextField(null=True, blank=True, verbose_name=_l('text'))
    trigger_action = models.CharField(max_length=2500, null=True, blank=True,
                                      verbose_name=_l('trigger action'))

    class Meta:
        abstract = True


class AdminNotificationTemplate(BaseTemplate):
    """
    Represents a "template of a template". This model is intended to be managed from administration, hence its name. It
    is identified by `slug`, which can be used for notification creation. However, this template is never used to
    directly render a notification, but instead is used to create `NotificationTemplate` with same values.

    Attributes:
        slug: Template slug, with which this template can be referred to.
    """
    slug = models.SlugField(max_length=200, unique=True, verbose_name=_l('slug'))

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
        title: Title of the notification.
        text: Text of the notification.
        trigger_action: Arbitrary action performed when user triggers (i.e. clicks/taps) the notification.
        admin_template: Reference to admin template that was used to create this notification template.
    """
    TEMPLATE_FIELDS = ['title', 'text', 'trigger_action']

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

    @property
    def slug(self):
        return self.admin_template.slug if self.admin_template else None

    def render(self, field, context):
        """
        Renders ``field`` using ``context``.
        """
        template_string = getattr(self, field) or ''

        if settings.TEMPLATE_TRANSLATE:
            template_string = _(template_string)

        if settings.TEMPLATE_CHECK:
            vars = re.findall(r'{{ ?([^\.}]+)[^}]*}}', template_string)
            for var in vars:
                value = context.get(var)
                if value is None or isinstance(value, DeletedRelatedObject):
                    raise MissingContextVariableError(field, var)

        return Template('{}{}'.format(settings.TEMPLATE_PREFIX, template_string)).render(Context(context))


class NotificationMeta(SmartModelBase, type):
    """
    Creates property for each template field. The property returns rendered template.
    """
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        for field in NotificationTemplate.TEMPLATE_FIELDS:
            setattr(
                new_class,
                field,
                property(lambda self, field=field: self._render(field))
            )

        return new_class


class Notification(BaseModel, metaclass=NotificationMeta):
    """
    Represents the notification.

    Attributes specified in ``NotificationTemplate.TEMPLATE_FIELDS`` are also available here, as generated properties,
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
    extra_data = models.TextField(null=True, blank=True, verbose_name=_l('extra data'))

    class Meta:
        verbose_name = _l('notification')
        verbose_name_plural = _l('notifications')
        ordering = ('-created_at',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._local_related_objects_dict = {}
        self._local_related_objects_list = []

    def _post_save(self, *args, **kwargs):
        """
        Saves local related objects into DB.
        """
        for name, obj in self._local_related_objects_dict.items():
            NotificationRelatedObject.objects.create(name=name, notification=self, content_object=obj)
        self._local_related_objects_dict = {}

        for obj in self._local_related_objects_list:
            NotificationRelatedObject.objects.create(notification=self, content_object=obj)
        self._local_related_objects_list = []

    def _check_related_objects_and_extra_data(self):
        """
        Checks type of local related objects and uniqueness of all related object's names compared to extra data.
        """
        local_related_objects = self._local_related_objects_list + [
            value for key, value in self._local_related_objects_dict.items()
        ]
        for obj in local_related_objects:
            if not isinstance(obj, models.Model):
                raise TypeError('Related object must be an instance of model.')

        db_related_object_names = [obj.name for obj in self.related_objects.filter(name__isnull=False)]
        common_keys = (
            set(self.get_extra_data()) & set(self._local_related_objects_dict)
            or set(self.get_extra_data()) & set(db_related_object_names)
            or set(self._local_related_objects_dict) & set(db_related_object_names)
        )
        if common_keys:
            raise ValueError('Conflicting keys found for related objects and/or extra data: {}'.format(
                ', '.join(common_keys)
            ))

    def _render(self, field):
        return self.template.render(field, self.context)

    def clean(self):
        self._check_related_objects_and_extra_data()

    @property
    def _get_secure_related_objects(self):
        """
        Returns dictionary of related objects for use in template context:
            * key is name of the related object and value is the object itself, wrapped in a security class.
            * local related objects and related objects from DB are combined together
            * related objects without name are skipped.
        """
        output = {}
        for obj in self.related_objects.filter(name__isnull=False):
            output[obj.name] = SecureRelatedObject(obj.content_object) if obj.content_object else DeletedRelatedObject()
        for name, obj in self._local_related_objects_dict.items():
            output[name] = SecureRelatedObject(obj)
        return output

    @cached_property
    def context(self):
        """
        Returns context dictionary used for rendering the template.
        """
        self._check_related_objects_and_extra_data()
        return {**self._get_secure_related_objects, **self.get_extra_data()}

    def set_extra_data(self, extra_data):
        """
        Setter for ``extra_data`` field.

        Arguments:
            extra_data: Dictionary of JSON serializable values.
        """
        if not isinstance(extra_data, dict):
            raise ValueError('Extra data must be a dictionary.')
        self.extra_data = json.dumps(extra_data, cls=DjangoJSONEncoder)

    def get_extra_data(self):
        """
        Getter for ``extra_data`` field.

        Returns:
            Dictionary with extra data.
        """
        return json.loads(self.extra_data) if self.extra_data is not None else {}

    def set_local_related_objects(self, related_objects):
        """
        Sets related objects locally. That means they can be used for rendering, but are not saved automatically.
        You must call `save()` in order to save them.
        """
        if isinstance(related_objects, dict):
            self._local_related_objects_dict = related_objects
        elif isinstance(related_objects, list):
            self._local_related_objects_list = related_objects
        else:
            raise TypeError('Related objects must be a list or dictionary in form {"name": object}.')


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
