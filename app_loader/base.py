
import warnings

from importlib import import_module  # noqa

from .utils import get_key_from_module, get_object, merge


class AppLoader(object):

    MODULES_AUTOLOAD = True

    CONFIG_MODULE_PREFIX = "LEONARDO"
    CONFIG_MODULE_SPEC_CLASS = "app_loader.spec.CONF_SPEC"
    CONFIG_MODULE_OBJECT_CLASS = "app_loader.config.Config"
    CONFIG_MASTER_OBJECT_CLASS = "app_loader.config.MasterConfig"

    def disable_autoload(self):
        self.MODULES_AUTOLOAD = False

    def enable_autoload(self):
        self.MODULES_AUTOLOAD = True

    def load_modules(self):
        """find all leonardo modules from environment"""
        if self.MODULES_AUTOLOAD:
            self.add_modules(self.find_modules())
        return self.modules

    @property
    def config_module_spec(self):
        """return config module spec dictionary"""
        return get_object(self.CONFIG_MODULE_SPEC_CLASS)

    @property
    def config_master_class(self):
        """return loaded master config class"""
        return get_object(self.CONFIG_MASTER_OBJECT_CLASS)

    @property
    def config_module_class(self):
        """return config class"""
        return get_object(self.CONFIG_MODULE_OBJECT_CLASS)

    @property
    def empty_config(self):
        """return inicialized config module class"""
        return self.config_module_class(self.config_module_spec)

    @property
    def blacklist(self):
        """return array of modules which would be ignored"""
        return ["haystack"]

    @property
    def is_loaded(self):
        return True if hasattr(self, '_modules') else False

    @property
    def modules(self):
        """loaded modules
        auto populated if is not present
        """
        return self._modules

    def set_modules(self, modules):
        """setter for modules"""
        self._modules = modules

    def add_modules(self, modules):
        """Merge new modules to loaded modules"""
        merged_modules = merge(modules, self.modules)
        self.set_modules(merged_modules)

    def get_modules(self):
        """load configuration for all modules"""
        if not hasattr(self, "loaded_modules"):
            _modules = []
            for mod in self.modules:
                mod_cfg = self.get_conf_from_module(mod)

                _modules.append((mod, mod_cfg,))

            _modules = sorted(_modules, key=lambda m: m[1].get('ordering'))

            self.loaded_modules = _modules
        return self.loaded_modules

    def get_modules_as_list(self):
        return [module_cfg for mod, module_cfg in self.get_modules()]

    @property
    def config(self):
        '''Master config'''
        if not hasattr(self, '_config'):
            self._config = self.config_master_class(
                self.get_modules(), self.empty_config)
        return self._config

    def get_app_modules(self, apps):
        """return array of imported leonardo modules for apps
        """
        modules = getattr(self, "_modules", [])

        if not modules:

            for app in apps:
                try:
                    # check if is not full app
                    _app = import_module(app)
                except ImportError:
                    _app = False

                if _app:
                    mod = _app

                if mod:
                    modules.append(mod)
                    continue

                warnings.warn('%s was skipped because app was '
                              'not found in PYTHONPATH' % app)

            self._modules = modules
        return self._modules

    @property
    def urlpatterns(self):
        '''load and decorate urls from all modules
        then store it as cached property for less loading
        '''

        # Django-specific: import django now
        from django.utils.module_loading import module_has_submodule  # noqa
        from django.conf.urls import include, patterns, url

        if hasattr(self, "_urlpatterns"):
            return self._urlpatterns

        urlpatterns = []
        # load all urls
        # support .urls file and urls_conf = 'elephantblog.urls' on default module
        # decorate all url patterns if is not explicitly excluded

        for mod in self.modules:
            # TODO this not work
            if self.is_leonardo_module(mod):

                conf = self.get_conf_from_module(mod)

                if module_has_submodule(mod, 'urls'):
                    urls_mod = import_module('.urls', mod.__name__)
                    if hasattr(urls_mod, 'urlpatterns'):
                        # if not public decorate all

                        if conf['public']:
                            urlpatterns += urls_mod.urlpatterns
                        else:
                            _decorate_urlconf(urls_mod.urlpatterns,
                                              require_auth)
                            urlpatterns += urls_mod.urlpatterns

        # avoid circural dependency
        # TODO use our loaded modules instead this property
        from django.conf import settings
        for urls_conf, conf in getattr(settings, 'MODULE_URLS', {}).items():
            # is public ?
            try:
                if conf['is_public']:
                    urlpatterns += \
                        patterns('',
                                 url(r'', include(urls_conf)),
                                 )
                else:
                    _decorate_urlconf(
                        url(r'', include(urls_conf)),
                        require_auth)
                    urlpatterns += patterns('',
                                            url(r'', include(urls_conf)))
            except Exception as e:
                raise Exception('raised %s during loading %s' %
                                (str(e), urls_conf))

        self._urlpatterns = urlpatterns
        return self._urlpatterns

    def is_leonardo_module(self, mod):
        """returns True if is our module
        """

        if hasattr(mod, 'default') \
                or hasattr(mod,
                           '{}_module_conf'.format(
                               self.CONFIG_MODULE_PREFIX.lower())):
            return True
        for key in dir(mod):
            if self.CONFIG_MODULE_PREFIX.upper() in key:
                return True
        return False

    def find_modules(self):
        """called when autoload is True and returns loaded modules

        check every installed module for config descriptor

        """

        if not hasattr(self, "_found_modules"):
            modules = []

            try:
                import pip
                installed_packages = pip.get_installed_distributions()
            except Exception:
                installed_packages = []
                warnings.warn(
                    'pip is not installed module, scan module is skipped.',
                    RuntimeWarning)

            for package in installed_packages:
                # check for default descriptor
                pkg_names = [k for k in package._get_metadata("top_level.txt")]
                for pkg_name in pkg_names:
                    if pkg_name not in self.blacklist:
                        try:
                            mod = import_module(pkg_name)
                            if hasattr(mod, 'default') \
                                    or hasattr(mod, 'leonardo_module_conf'):
                                modules.append(mod)
                                continue
                            for key in dir(mod):
                                if 'LEONARDO' in key:
                                    modules.append(mod)
                                    break
                        except Exception:
                            pass
            self._found_modules = modules
        return self._found_modules

    def get_conf_from_module(self, mod):
        """return configuration from module with defaults no worry about None type

        """

        conf = self.empty_config

        # get imported module
        mod = self.find_config_module(mod)

        conf.set_module(mod)

        # extarct from default object or from module
        if hasattr(mod, 'default'):
            default = mod.default
            conf = self.extract_conf_from(default, conf)
        else:
            conf = self.extract_conf_from(mod, conf)
        return conf

    def find_config_module(self, mod):
        """returns imported module
        check if is ``leonardo_module_conf`` specified and then import them
        """

        module_location = getattr(
            mod, 'leonardo_module_conf',
            getattr(mod, "LEONARDO_MODULE_CONF", None))
        if module_location:
            mod = import_module(module_location)

        elif hasattr(mod, 'default_app_config'):
            # use django behavior
            mod_path, _, cls_name = mod.default_app_config.rpartition('.')
            _mod = import_module(mod_path)
            config_class = getattr(_mod, cls_name)
            # check if is leonardo config compliant
            if self.is_leonardo_module(config_class):
                mod = config_class

        return mod

    def extract_conf_from(self, mod, conf, depth=0, max_depth=2):
        """recursively extract keys from module or object
        by passed config scheme
        """

        # extract config keys from module or object
        for key, default_value in conf.items():
            conf[key] = get_key_from_module(mod, key, default_value)

        # support for recursive dependecies
        try:
            filtered_apps = [
                app for app in conf['apps'] if app not in self.blacklist]
        except TypeError:
            pass
        except Exception as e:
            warnings.warn('Error %s during loading %s' % (e, conf['apps']))

        for app in filtered_apps:
            try:
                app_module = import_module(app)
                if app_module != mod:
                    app_module = self.find_config_module(app_module)
                    if depth < max_depth:
                        mod_conf = self.extract_conf_from(
                            app_module, conf=self.empty_config, depth=depth + 1)
                        for k, v in mod_conf.items():
                            # prevent config duplicity
                            # skip config merge
                            if k == 'config':
                                continue
                            if isinstance(v, dict):
                                conf[k].update(v)
                            elif isinstance(v, (list, tuple)):
                                conf[k] = merge(conf[k], v)
            except Exception as e:
                pass  # swallow, but maybe log for info what happens
        return conf

    _instance = None

    def __new__(cls, *args, **kwargs):
        """A singleton implementation of AppLoader. There can be only one.
        """
        if not cls._instance:
            cls._instance = super(AppLoader, cls).__new__(cls, *args, **kwargs)
        return cls._instance
