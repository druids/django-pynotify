.. highlight:: shell

============
Installation
============


Stable release
--------------

To install PyNotify, run this command in your terminal:

.. code-block:: console

    $ pip install django-pynotify

This is the preferred method of installation, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/druids/django-pynotify

Or download the `tarball`_:

.. code-block:: console

    $ curl -OL https://github.com/druids/django-pynotify/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ make install


.. _Github repo: https://github.com/druids/django-pynotify
.. _tarball: https://github.com/druids/django-pynotify/tarball/master


Enable the library
------------------

Once installed, add the library to ``INSTALLED_APPS`` in your Django project settings::

    INSTALLED_APPS = [
        ...
        'pynotify.apps.PyNotifyConfig'
    ]
