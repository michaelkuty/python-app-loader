
=================
python-app-loader
=================

Load configs from python modules or Django applications.

.. contents::
    :local:

Installation
============

.. code-block:: bash

    pip install python-app-loader


Usage
=====

Your settings.py

.. code-block:: python

    from app_loader import app_loader

    APPS = ['testapp']

    # load directly specified apps
    app_loader.get_app_modules(APPS)

    # load all modules
    app_loader.load_modules()

    # just propagate all loaded modules to settings
    INSTALLED_APPS = app_loader.config.apps

    # override all
    try:
        from local_settings import *
    except ImportError:
        pass


Read More
=========

* https://github.com/django-leonardo/django-leonardo
