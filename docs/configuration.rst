.. _config:

=============
Configuration
=============

You can configure the library in Django settings. Following options are available:

* ``PYNOTIFY_AUTOLOAD_APPS`` (default: ``None``)

    Iterable of Django apps that will be scanned for ``handlers`` module at startup. If the module is found, it will be
    imported, i.e. causing notification handlers to be automatically loaded.

* ``PYNOTIFY_CELERY_TASK`` (default: ``pynotify.tasks.notification_task``)

    Import path to a Celery task used in asynchronous mode. See :ref:`async`.

* ``PYNOTIFY_ENABLED`` (default: ``True``)

    Boolean indicating if library functionality, i.e. creating of notifications, is enabled. More specifically, if set to
    ``False``, receiver will not be called upon signal reception.

* ``PYNOTIFY_RECEIVER`` (default: ``pynotify.receivers.SynchronousReceiver``)

    Import path to a receiver class.

* ``PYNOTIFY_RELATED_OBJECTS_ALLOWED_ATTRIBUTES`` (default: ``{'get_absolute_url', }``)

    A set of related object's attributes that can be used in notification template(s).

* ``PYNOTIFY_TEMPLATE_CHECK`` (default: ``False``)

    Boolean indicating if template string should be checked before rendering. If any named related object or extra data
    used in the template string is missing, :class:`~pynotify.exceptions.MissingContextVariableError` will be raised.

* ``PYNOTIFY_TEMPLATE_PREFIX`` (default: ``''``)

    String that is prepended to any template just before rendering. Can be used to load custom tags/filters.

* ``PYNOTIFY_TEMPLATE_TRANSLATE`` (default: ``False``)

    Boolean indicating if template string should be translated via ``ugettext()`` before rendering.
