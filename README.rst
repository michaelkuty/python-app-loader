
=================
python-app-loader
=================

Load configs from python modules especially Django applications. Plays well with Django application/modules. You can simply define your specification and then just load your modules which tells you what needs. It's universal and easy to use.

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


You can inicialize your AppLoader::

    loader = AppLoader(autoload=False)

    loader.get_app_modules(APPS)

    print(loader.config.apps)

or you can create your own AppLoader::

    class MyAppLoader(AppLoader):

        CONFIG_MASTER_OBJECT_CLASS = 'mymodule.MyMasterClass'


For advance example check django-leonardo which uses this module for loading configurations from all modules. (about 60+ modules) which could be auto loaded without any requirements.

Read More
=========

* https://github.com/django-leonardo/django-leonardo
