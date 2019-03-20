from django.dispatch import Signal


article_viewed = Signal(providing_args=['user', 'article'])
