import datetime
import pytz
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils.translation import override, gettext_noop
from chamber.exceptions import PersistenceException

from pynotify.exceptions import MissingContextVariableError
from pynotify.helpers import DeletedRelatedObject, SecureRelatedObject
from pynotify.models import AdminNotificationTemplate, Notification, NotificationTemplate

from articles.models import Article


class AdminNotificationTemplateTestCase(TestCase):

    def test_admin_template_should_have_string_representation(self):
        template = AdminNotificationTemplate.objects.create(
            title='Hello!',
            slug='test-template',
        )
        self.assertEqual(str(template), 'admin notification template #{} ({})'.format(
            template.pk,
            template.slug,
        ))


class NotificationTemplateTestCase(TestCase):

    def setUp(self):
        template = gettext_noop('New article: {{article}}')

        # set same template to all fields
        self.template = NotificationTemplate.objects.create(
            **{
                field: {'abc': template} if field == 'extra_fields' else template
                for field in NotificationTemplate.TEMPLATE_FIELDS
            }
        )
        self.context = {
            'article': Article.objects.create(
                title='The Old Witch',
                author=User.objects.create_user('John')
            )
        }

    def render(self, field, context=None):
        return self.template.render(field, self.context if context is None else context)

    def test_template_fields_should_be_rendered_as_html(self):
        TEMPLATE_STRING = 'New article: <b>{{article}}</b>'
        RENDERED_STRING = 'New article: <b>Good &amp; Ugly</b>'

        self.context['article'].change_and_save(title='Good & Ugly')

        for field in NotificationTemplate.TEMPLATE_FIELDS:
            setattr(self.template, field, {'abc': TEMPLATE_STRING} if field == 'extra_fields' else TEMPLATE_STRING)
            self.assertEqual(
                self.render(field),
                {'abc': RENDERED_STRING} if field == 'extra_fields' else RENDERED_STRING
            )

    @override_settings(PYNOTIFY_TEMPLATE_CHECK=True)
    def test_template_should_be_checked(self):
        # check multiple types of missing variable
        with self.assertRaises(MissingContextVariableError):
            self.render('title', {})
        with self.assertRaises(MissingContextVariableError):
            self.render('title', {'article': None})
        with self.assertRaises(MissingContextVariableError):
            self.render('title', {'article': DeletedRelatedObject()})

        # check multiple formats of single variable
        for template in ('Article: {{article}}', 'Article: {{ article }}', 'Article: {{ article|safe }}'):
            self.template.change_and_save(text=template)
            self.assertEqual(self.render('text', {'article': 'abc'}), 'Article: abc')
            with self.assertRaises(MissingContextVariableError):
                self.render('text', {})

        # check multiple formats of nested variable
        for template in (
            'Author: {{article.author}}',
            'Author: {{ article.author }}',
            'Author: {{ article.author|safe }}',
        ):
            self.template.change_and_save(text=template)
            self.assertEqual(self.render('text', {'article': {'author': 'abc'}}), 'Author: abc')
            with self.assertRaises(MissingContextVariableError):
                self.render('text', {'article': {}})

        # test with setting off
        with override_settings(PYNOTIFY_TEMPLATE_CHECK=False):
            self.assertEqual(self.render('title', {}), 'New article: ')
            self.assertEqual(self.render('title', {'article': None}), 'New article: None')
            self.assertEqual(self.render('title', {'article': DeletedRelatedObject()}), 'New article: [DELETED]')

    @override_settings(PYNOTIFY_TEMPLATE_CHECK=True)
    def test_template_check_should_detect_multiple_variable_formats(self):
        TEMPLATES = ['{{abcd}}', '{{ abcd }}', '{{abcd.efgh}}', '{{ abcd.efgh }}']
        for template in TEMPLATES:
            self.template.title = template
            self.template.save()
            with self.assertRaises(MissingContextVariableError):
                self.render('title')

    @override_settings(PYNOTIFY_TEMPLATE_TRANSLATE=True)
    def test_template_should_be_translated(self):
        with override('cs'):
            self.assertEqual(self.render('title'), 'Nový článek: The Old Witch')

            # test with setting off
            with override_settings(PYNOTIFY_TEMPLATE_TRANSLATE=False):
                self.assertEqual(self.render('title'), 'New article: The Old Witch')

    @override_settings(PYNOTIFY_TEMPLATE_PREFIX='{% load example_tags %}')
    def test_template_should_be_prefixed_with_string_from_configuration(self):
        self.template.title = '{% greeting %}'
        self.assertEqual(self.render('title'), 'Howdy!')

    def test_template_should_have_string_representation(self):
        self.assertEqual(str(self.template), 'notification template #{}'.format(self.template.pk))

    def test_template_should_return_slug_of_the_admin_template(self):
        self.assertEqual(self.template.slug, None)
        self.template.admin_template = AdminNotificationTemplate.objects.create(title='Hello!', slug='test-template')
        self.assertEqual(self.template.slug, 'test-template')

    @override_settings(PYNOTIFY_STRIP_HTML=True)
    def test_template_should_strip_html_during_rendering_if_enabled(self):
        for field in NotificationTemplate.TEMPLATE_FIELDS:
            for input_value, output_value in [
                (
                    'My name is <b>John</b> and I like <a href="http://food.com">food</a>.',
                    'My name is John and I like food.',
                ),
                ('<svg/onload=alert("XSS")>', ''),
                ('Tom &amp; Jerry', 'Tom & Jerry'),
                ('45&nbsp;USD', '45\xa0USD'),
            ]:
                if field == 'extra_fields':
                    input_value = {'abc': input_value}
                    output_value = {'abc': output_value}

                setattr(self.template, field, input_value)
                self.assertEqual(self.render(field), output_value)

    def test_extra_fields_should_be_dictionary(self):
        with self.assertRaises(PersistenceException):
            self.template.change_and_save(extra_fields=1000)


class NotificationTestCase(TestCase):

    def setUp(self):
        self.recipient = User.objects.create_user('Bill')
        self.author = User.objects.create_user('John')
        self.article = Article.objects.create(title='The Old Witch', author=self.author)
        self.random_user = User.objects.create_user('Mr.Random')

        self.template = NotificationTemplate.objects.create(
            title='{{article}}',
            text='{{author}} created a new article named {{article}}.',
            trigger_action='{{article.get_absolute_url}}',
            extra_fields = {'abc': 'def:{{some_value}}'}
        )

        self.notification = Notification.objects.create(
            recipient=self.recipient,
            template=self.template,
            related_objects={
                'article': self.article,
                'author': self.article.author,
                'random_user': self.random_user,
            },
            extra_data={
                'some_value': 123,
                'decimal_value': Decimal('1.55'),
                'datetime': datetime.datetime(2022, 1, 1, 12, 0, 0, 0, pytz.UTC)
            }
        )

    def test_generated_fields_should_use_template_for_rendering(self):
        self.assertEqual(self.notification.title, 'The Old Witch')
        self.assertEqual(self.notification.text, 'John created a new article named The Old Witch.')
        self.assertEqual(self.notification.trigger_action, '/articles/1/')
        self.assertEqual(self.notification.extra_fields['abc'], 'def:123')

        self.author.username = 'James'
        self.author.save()

        self.article.title = 'The King Of The Cats'
        self.article.save()

        self.template.title = 'New article: {{article}}'
        self.template.save()

        self.notification.refresh_from_db()

        self.assertEqual(self.notification.title, 'New article: The King Of The Cats')
        self.assertEqual(self.notification.text, 'James created a new article named The King Of The Cats.')

    def test_extra_data_should_be_dictionary(self):
        with self.assertRaises(PersistenceException):
            self.notification.change_and_save(extra_data=1000)

    def test_related_objects_and_extra_data_should_not_contain_same_keys(self):
        with self.assertRaises(PersistenceException):
            self.notification.change_and_save(extra_data={'article': 123})

    def test_context_should_contain_related_objects_as_proxies_and_extra_data(self):
        ctx = self.notification.refresh_from_db().context

        self.assertTrue(isinstance(ctx['article'], SecureRelatedObject))
        self.assertEqual(ctx['article']._object, self.article)

        self.assertTrue(isinstance(ctx['author'], SecureRelatedObject))
        self.assertEqual(ctx['author']._object, self.article.author)

        self.assertTrue(isinstance(ctx['random_user'], SecureRelatedObject))
        self.assertEqual(ctx['random_user']._object, self.random_user)

        self.assertEqual(ctx['some_value'], 123)
        self.assertEqual(ctx['decimal_value'], '1.55')
        self.assertEqual(ctx['datetime'], '2022-01-01T12:00:00Z')

    def test_context_should_be_cached(self):
        self.assertEqual(
            id(self.notification.context),
            id(self.notification.context),
        )

    def test_context_should_contain_placeholder_object_for_deleted_related_object(self):
        self.random_user.delete()
        self.notification.refresh_from_db()
        self.assertTrue(isinstance(self.notification.context['random_user'], DeletedRelatedObject))

    def test_creating_notification_should_not_be_possible_with_related_objects_in_invalid_format(self):
        INVALID_RELATED_OBJECTS = (
            self.random_user,
            User.objects.all(),
            'abc',
            ['abc', 'abc'],
            {'abc': 'abc'},
        )
        for related_objects in INVALID_RELATED_OBJECTS:
            with self.assertRaises(TypeError):
                Notification.objects.create(
                    recipient=self.recipient,
                    template=self.template,
                    related_objects=related_objects
                )

    def test_creating_notification_should_allow_list_of_related_objects(self):
        notification = Notification.objects.create(
            recipient=self.recipient,
            template=self.template,
            related_objects=[self.random_user],
        )

        self.assertEqual(notification.related_objects.count(), 1)
        related_object = notification.related_objects.get()
        self.assertEqual(related_object.name, None)
        self.assertEqual(related_object.content_object, self.random_user)
        self.assertEqual(notification.context, {})

    def test_notification_should_have_string_representation(self):
        self.assertEqual(str(self.notification), 'notification #{}'.format(self.notification.pk))

    def test_notification_should_be_filtered_with_related_object(self):
        # random user is related object
        self.assertEqual(Notification.objects.filter_with_related_object(self.random_user).count(), 1)
        self.assertEqual(Notification.objects.filter_with_related_object(self.author)[0], self.notification)
        # recipient is not related object
        self.assertFalse(Notification.objects.filter_with_related_object(self.recipient).exists())
