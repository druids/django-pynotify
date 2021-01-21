#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'beautifulsoup4 ~=4.8.0',
    'celery >= 4.2.0',
    'django >= 2.2',
    'django-chamber >= 0.5.0',
    'lxml >= 4.6.2',
]

setup(
    author="Ondřej Kulatý",
    author_email='kulaty.o@gmail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="General purpose notification library for Django",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='django-pynotify',
    name='django-pynotify',
    packages=find_packages(include=['pynotify']),
    url='https://github.com/druids/django-pynotify',
    version='0.4.5',
    zip_safe=False,
)
