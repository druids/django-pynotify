from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.signals import post_save

from pynotify.handlers import BaseHandler

from articles.models import Article
from articles.signals import article_viewed


class BaseArticleHandler(BaseHandler):
    """
    Base handler with common logic for Article created/update notifications.
    """
    def get_recipients(self):
        # broadcast to everyone except article author
        return User.objects.filter(~Q(pk=self.signal_kwargs['instance'].author.pk))

    def get_template_data(self):
        return {
            'title': self.get_title(),
            'trigger_action': '{{article.get_absolute_url}}'
        }

    def get_related_objects(self):
        return {
            'article': self.signal_kwargs['instance'],
            'author': self.signal_kwargs['instance'].author
        }

    class Meta:
        abstract = True
        signal = post_save
        allowed_senders = (Article,)


class ArticleCreatedHandler(BaseArticleHandler):
    """
    Creates a notification when a new Article is created.
    """
    def get_title(self):
        return '<b>{{author}}</b> created a new article {{article}}'

    def handle(self, signal_kwargs):
        if signal_kwargs['created']:
            return super().handle(signal_kwargs)


class ArticleUpdatedHandler(BaseArticleHandler):
    """
    Creates a notification when existing Article is updated.
    """
    def get_title(self):
        return '<b>{{author}}</b> updated article {{article}}'

    def handle(self, signal_kwargs):
        if not signal_kwargs['created']:
            return super().handle(signal_kwargs)


class ArticleViewedHandler(BaseHandler):
    """
    Creates a notification when user reads an article.
    """
    def get_recipients(self):
        return [self.signal_kwargs['article'].author]

    def get_template_data(self):
        return {
            'title': '<b>{{user}}</b> viewed your article {{article}}',
            'trigger_action': '{{article.get_absolute_url}}'
        }

    def get_related_objects(self):
        return {k: v for k, v in self.signal_kwargs.items() if k in ('user', 'article')}

    class Meta:
        signal = article_viewed
