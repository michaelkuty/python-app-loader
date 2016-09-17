
from __future__ import absolute_import, unicode_literals

from django.test import TestCase
from django.conf import settings
from app_loader import app_loader


class CommandTest(TestCase):

    def test_01_app_loader(self):

        app_loader.disable_autoload()

        self.assertEqual(len(app_loader.modules), 1)

        modules = app_loader.get_modules()

        self.assertEqual(settings.LEONARDO_MODULES, modules)

        testapp, config = modules[0]

        self.assertEqual(hasattr(config, 'apps'), True)

        self.assertIn('testapp', config.apps)
        self.assertIn('testapp', config.module_name)
        self.assertIn('testapp', config.name)

    def test_01_custom_app(self):

        app_loader._modules = []

        app_loader.enable_autoload()

        app_loader.get_app_modules(['testapp'])
        app_loader.load_modules()

        self.assertIn('testapp', app_loader.config.apps)
        self.assertIn('GOOGLE_ANALYTICS_SITE_SPEED', app_loader.config.config)
        self.assertIsInstance(app_loader.config.config, dict)

        with self.assertRaises(KeyError):
            app_loader.config.hovno

        # just propagate all loaded modules to settings
        modules = app_loader.get_modules()

        self.assertEqual(len(app_loader.modules), 4)

        #self.assertIn('leonardo_multisite', app_loader.modules[1][1].apps)

        testapp, config = modules[0]

        self.assertEqual(config.module, testapp)

        self.assertIn('testapp', config.apps)


    def test_02_custom_classes(self):

        from app_loader.config import Config, MasterConfig
        self.assertIsInstance(app_loader.empty_config, Config)

        self.assertIsInstance(app_loader.config, MasterConfig)


    def test_03_utils(self):

        from app_loader.utils import merge

        array = ["one", "two"]
        array1 = ["one"]
        self.assertEqual(merge(array, array1), ["one", "two"])
        self.assertEqual(merge(array1, array), ["one", "two"])

        dic = {"test1": "value", "test2": "hello"}
        dic1 = {"test1": "value", "test3": "hello"}

        self.assertEqual(merge(dic, dic1), {"test1": "value", "test3": "hello", "test2": "hello"})
        self.assertEqual(merge(dic1, dic), {"test1": "value", "test3": "hello", "test2": "hello"})


    def test_04_urlpatterns(self):

        from app_loader import app_loader

        # TODO test reverse and decorator
        app_loader.urlpatterns