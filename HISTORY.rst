=======
History
=======

0.1.7 (2020-01-20)
----------------

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
