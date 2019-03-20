from chamber.models import SmartModel
from django.conf import settings
from django.db import models
from django.urls import reverse


class Article(SmartModel):

    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='articles', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    text = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('article_detail', kwargs={'pk': self.pk})

    class Meta:
        ordering = ('-created_at',)
