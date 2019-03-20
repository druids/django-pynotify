Example project
===============

You can quickly try the library in the included example project. Install the library for development, as described in
:ref:`contrib` and run following commands::

    $ cd example
    $ ./manage.py runserver

The example project will be available at https://localhost:8000/.

Asynchronous operation
----------------------

If you want to try :ref:`async` in the example project, make sure you have Redis installed and uncomment following
settings in ``example/config/settings.py``::

  CELERY_BROKER_URL = 'redis://127.0.0.1'
  PYNOTIFY_RECEIVER = 'pynotify.receivers.AsynchronousReceiver'

Then open a new terminal window and start Celery with::

    $ cd example
    $ celery -A config worker
