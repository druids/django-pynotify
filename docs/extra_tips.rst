==========
Extra tips
==========

Simplified usage
----------------

If all you need is just to create notifications at some point in your code, you can start doing so right away after
installation of the library. No further configuration needed!

To create a notification, simply call the :func:`~pynotify.notify.notify` function::

    from django.contrib.auth.models import User
    from pynotify.notify import notify

    notify(recipients=User.object.all(), title='Hello World!')

Even with this simple approach, you can still use templating and/or translations.

Translations
------------

Notification templates can be translated using the standard Django translation mechanism. The only thing needed is to
enable template translation by setting ``PYNOTIFY_TEMPLATE_TRANSLATE`` to ``True`` and include the translated messages
in ``*.po`` files.

You can use ``ugettext_noop()`` when defining template strings, so the string will be automatically included in the
transaltion file(s)::


    def get_template_data(self):
        return {
            'title': ugettext_noop('{{user}} viewed your article {{article}}'),
        }


However keep in mind, that if you change the template string inside ``ugettext_noop()``, you either have to change the
corresponding notification template saved in the database (e.g. using data migration) or keep the old string
in the translation file.

In case you are using **template slugs**, just put ``ugettext_noop()`` anywhere in the code and keep it in sync with
contents of the notification template saved in the database::

    class ArticleViewedHandler(BaseHandler):

        template_slug = 'article-viewed'

        # title translation
        ugettext_noop('{{user}} viewed your article {{article}}')

.. _async:

Asynchronous operation
----------------------

Creating notifications can be time demanding, especially when creating a lot of notifications at once or dispatching via
3rd party services (e.g. SMS, e-mails, push). Using the default synchronous operation in these cases considerably
extends time needed to process a request. Therefore, **it is recommended to always switch to asynchronous mode, if you
can.**

The library contains :class:`~pynotify.receivers.AsynchronousReceiver`, which allows asynchronous operation. Intead of
calling a handler directly, it works by passing serialized signal kwargs to a Celery task upon database transaction
commit and the task then calls the handler. Since serialization comes into play here, signal kwargs are restricted
to be either directly JSON serializable values or model instances (which are serialized using built-in
:class:`~pynotify.serializers.ModelSerializer`).

To go asynchronous, change setting ``PYNOTIFY_RECEIVER`` to ``pynotify.receivers.AsynchronousReceiver`` and start Celery
in your project in autodiscover mode. See http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html.

The Celery task is defined in the library, you don't have to create one. But in case you want to use a custom Celery
task, set its import path to ``PYNOTIFY_CELERY_TASK`` setting. Your custom task should grab all the arguments it
receives and pass them to :func:`~pynotify.helpers.process_task`, like this::

    from pynotify.helpers import process_task

    @shared_task
    def my_task(*args, **kwargs):
        process_task(*args, **kwargs)
