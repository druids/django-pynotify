from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils.translation import ugettext_noop, activate

from pynotify.exceptions import MissingContextVariableError
from pynotify.models import Notification, NotificationTemplate

from articles.models import Article


class NotificationTemplateTestCase(TestCase):

    def setUp(self):
        template = ugettext_noop('New article: {{article}}')

        # set same template to all fields
        self.template = NotificationTemplate.objects.create(
            **{field: template for field in NotificationTemplate.TEMPLATE_FIELDS}
        )
        self.context = {
            'article': Article.objects.create(
                title='The Old Witch',
                author=User.objects.create_user('John')
            )
        }

    def render(self, field, context=None):
        return self.template.render(field, self.context if context is None else context)

    def test_template_fields_should_be_rendered(self):
        for field in NotificationTemplate.TEMPLATE_FIELDS:
            self.assertEqual(self.render(field), 'New article: The Old Witch')

    @override_settings(PYNOTIFY_TEMPLATE_CHECK=True)
    def test_template_should_be_checked(self):
        with self.assertRaises(MissingContextVariableError):
            self.render('title', {})

        with self.assertRaises(MissingContextVariableError):
            self.render('title', {'article': None})

        # test with setting off
        with override_settings(PYNOTIFY_TEMPLATE_CHECK=False):
            self.assertEqual(self.render('title', {}), 'New article: ')
            self.assertEqual(self.render('title', {'article': None}), 'New article: None')

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
        activate('cs')

        self.assertEqual(self.render('title'), 'Nový článek: The Old Witch')

        # test with setting off
        with override_settings(PYNOTIFY_TEMPLATE_TRANSLATE=False):
            self.assertEqual(self.render('title'), 'New article: The Old Witch')

        activate('en')


class NotificationTestCase(TestCase):

    def setUp(self):
        self.recipient = User.objects.create_user('Bill')
        self.author = User.objects.create_user('John')
        self.article = Article.objects.create(title='The Old Witch', author=self.author)
        self.random_user = User.objects.create_user('Mr.Random')

        self.template = NotificationTemplate.objects.create(
            title='{{article}}',
            text='{{article.author}} created a new article named {{article}}.',
            trigger_action='{{article.get_absolute_url}}',
        )

        self.notification = Notification.objects.create(
            recipient=self.recipient,
            template=self.template,
            related_objects={
                'article': self.article,
                'random_user': self.random_user,
            },
        )

    def test_generated_fields_should_use_template_for_rendering(self):
        self.assertEqual(self.notification.title, 'The Old Witch')
        self.assertEqual(self.notification.text, 'John created a new article named The Old Witch.')
        self.assertEqual(self.notification.trigger_action, '/articles/1/')

        self.author.username = 'James'
        self.author.save()

        self.article.title = 'The King Of The Cats'
        self.article.save()

        self.template.title = 'New article: {{article}}'
        self.template.save()

        self.notification.refresh_from_db()

        self.assertEqual(self.notification.title, 'New article: The King Of The Cats')
        self.assertEqual(self.notification.text, 'James created a new article named The King Of The Cats.')

    def test_context_should_contain_related_objects(self):
        self.assertEqual(self.notification._context, {'article': self.article, 'random_user': self.random_user})

    def test_context_should_be_cached(self):
        # force context to load
        self.notification._context
        self.random_user.username = 'Mr.Random2'
        self.random_user.save()

        self.assertEqual(self.notification._context['random_user'].username, 'Mr.Random')

        self.notification.refresh_from_db()
        self.assertEqual(self.notification._context['random_user'].username, 'Mr.Random2')

    def test_context_should_not_contain_deleted_objects(self):
        self.random_user.delete()
        self.notification.refresh_from_db()
        self.assertEqual(self.notification._context, {'article': self.article, 'random_user': None})

    def test_creating_notification_should_not_be_possible_with_related_objects_in_invalid_format(self):
        INVALID_RELATED_OBJECTS = (
            self.random_user,
            [self.random_user, self.author],
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
