=======
History
=======

not released yet
----------------

* Add ``is_active`` flag to ``AdminNotificationTemplate`` model

0.3.1 (2020-06-12)
------------------

* Improve template variable checking
* Add new filter ``filter_with_related_object``

0.3.0 (2020-04-19)
------------------

* Fix documentation
* Change ``PYNOTIFY_AUTOLOAD_APPS`` to ``PYNOTIFY_AUTOLOAD_MODULES``, i.e. allow notification handlers to reside in
  arbitrary module

0.2.2 (2020-02-11)
------------------

* Use Django JSON encoder for encoding extra data

0.2.1 (2020-02-11)
------------------

* Fix failed PyPi upload

0.2.0 (2020-02-11)
------------------

* Add admin templates
* Limit usage of related objects in templates and add ``PYNOTIFY_RELATED_OBJECTS_ALLOWED_ATTRIBUTES`` setting
* Show placeholder text for deleted related objects

0.1.7 (2020-01-20)
------------------

* Add support for Python 3.8 and Django 2.2
* Fix generating of translations
* Allow unnamed related objects to be passed in a list

0.1.6 (2019-04-16)
------------------

* Add ``PYNOTIFY_TEMPLATE_PREFIX`` config option
* Add methods ``get_template_slug()`` and ``get_dispatcher_classes()`` to ``BaseHandler``
* Add coveralls.io integration

0.1.5 (2019-04-12)
------------------

* Add extra data to ``Notification`` model

0.1.4 (2019-04-08)
------------------

* Add ``_can_handle()`` method to ``BaseHandler``
* Add ``PYNOTIFY_ENABLED`` setting

0.1.3 (2019-04-01)
------------------

* Add ``kwargs`` to Notification manager's ``create()`` method
* Add ``realted_objects_dict`` property to ``Notification`` model

0.1.2 (2019-03-20)
------------------

* Remove automatic deploy to PyPi from Travis

0.1.1 (2019-03-20)
------------------

* First release of the library
