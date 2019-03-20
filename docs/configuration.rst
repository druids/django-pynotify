.. _config:

=============
Configuration
=============

You can configure the library in Django settings. Following options are available:

* ``PYNOTIFY_AUTOLOAD_APPS`` (default: ``None``)

    Iterable of Django apps that will be scanned for ``handlers`` module at startup. If the module is found, it will be
    imported, i.e. causing notification handlers to be automatically loaded.

* ``PYNOTIFY_CELERY_TASK`` (default: ``pynotify.tasks.pynotify_task``)

    Import path to a Celery task used in asynchronous mode. See :ref:`async`.

* ``PYNOTIFY_RECEIVER`` (default: ``pynotify.receivers.SynchronousReceiver``)

    Import path to a receiver class.

* ``PYNOTIFY_TEMPLATE_CHECK`` (default: ``False``)

    Boolean indicating if template string should be checked before rendering. If any related object used in the template
    string is missing, :class:`~pynotify.exceptions.MissingContextVariableError` will be raised.

* ``PYNOTIFY_TEMPLATE_TRANSLATE`` (default: ``False``)

    Boolean indicating if template string should be translated via ``ugettext()`` before rendering.
