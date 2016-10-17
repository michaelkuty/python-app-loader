
import warnings

from importlib import import_module  # noqa

from .utils import get_key_from_module, get_object, merge, _decorate_urlconf


class AppLoader(object):

    # check all modules automaticaly
    MODULES_AUTOLOAD = True

    # config prefix
    CONFIG_PREFIX = "LEONARDO"

    # config specification schema
    CONFIG_MODULE_SPEC_CLASS = "app_loader.spec.CONF_SPEC"

    # base class inicialized from config, based on dictionary
    CONFIG_MODULE_OBJECT_CLASS = "app_loader.config.Config"

    # this class is used to encapsualtion of all loaded configs
    CONFIG_MASTER_OBJECT_CLASS = "app_loader.config.MasterConfig"

    # check keys which are not in the config spec
    CHECK_UNDEFINED_KEYS = True
    # use keys which are not in the config spec
    # add new keys into config spec and reload all modules
    # this process can slow down booting your app and it's recommended
    # add this keys into config spec
    USE_UNDEFINED_KEYS = True

    # array of tuples where [(key, value)]
    undefined_keys = []

    def __init__(self, autoload=True, prefix="leonardo",
                 use_undefined_key=True, check_undefined_keys=True,
                 master_class="app_loader.config.MasterConfig",
                 module_class="app_loader.config.Config",
                 spec_class="app_loader.spec.CONF_SPEC"):

        self.MODULES_AUTOLOAD = autoload
        self.CONFIG_PREFIX = prefix
        self.USE_UNDEFINED_KEYS = use_undefined_key
        self.CHECK_UNDEFINED_KEYS = use_undefined_key
        self.CONFIG_MODULE_SPEC_CLASS = spec_class
        self.CONFIG_MODULE_OBJECT_CLASS = module_class
        self.CONFIG_MASTER_OBJECT_CLASS = master_class

    def load_modules(self):
        """find all leonardo modules from environment"""
        if self.MODULES_AUTOLOAD:
            self.add_modules(self.find_modules())
        return self.modules

    @property
    def config_module_spec(self):
        """return config module spec dictionary

        note: updated config spec if undefined_keys are available
        and enabled
        """
        spec = get_object(self.CONFIG_MODULE_SPEC_CLASS)

        if self.new_keys:

            for key_and_value in self.undefined_keys:
                # TODO: check type and use empty value
                spec[key_and_value[0]] = key_and_value[1]

        return spec

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

            # we have new keys, start new loading now
            if len(self.undefined_keys) > 0 and self.USE_UNDEFINED_KEYS:
                warnings.warn('We found new keys(%s) and start '
                              'loading again...'
                              "It's recommended add new keys into "
                              "%s_CONFIG_SPEC" % (self.undefined_keys,
                                                  self.CONFIG_PREFIX))
                _modules = []

                for mod in self.modules:
                    mod_cfg = self.get_conf_from_module(mod)
                    _modules.append((mod, mod_cfg,))

            # sort modules by ordering key
            _modules = sorted(_modules, key=lambda m: m[1].get('ordering'))

            self.loaded_modules = _modules
        return self.loaded_modules

    def get_modules_as_list(self):
        return [module_cfg for mod, module_cfg in self.get_modules()]

    @property
    def new_keys(self):
        '''Just indicator for no cache'''
        if self.CHECK_UNDEFINED_KEYS \
                and self.USE_UNDEFINED_KEYS \
                and len(self.undefined_keys) > 0:
            return True
        return False

    @property
    def config(self):
        '''Master config'''
        if not hasattr(self, '_config') or self.new_keys:
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

    def is_leonardo_module(self, mod):
        """returns True if is our module
        """

        if hasattr(mod, 'default') \
                or hasattr(mod,
                           '{}_module_conf'.format(
                               self.CONFIG_PREFIX.lower())):
            return True

        for key in dir(mod):
            if self.CONFIG_PREFIX.upper() in key:
                return True

        return False

    def find_modules(self):
        """called when autoload is True and returns loaded modules

        check every installed module for config descriptor

        """

        if not hasattr(self, "_found_modules"):
            modules = []

            try:
                import pkgutil
                installed_packages = [p[1]
                                      for p in pkgutil.iter_modules()
                                      if p[2]]
            except Exception:
                installed_packages = []
                warnings.warn(
                    'error during auto loading modules,'
                    ' scan module is skipped.',
                    RuntimeWarning)

            for pkg_name in installed_packages:
                # check for default descriptor
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
                        if hasattr(mod, 'default_app_config'):
                            for key in dir(mod):
                                if key in self.empty_config.keys():
                                    mod = get_object(mod.default_app_config)
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

    def _get_undefiend_keys(self, mod, conf):
        '''return keys which are recognized but are not in schema'''
        undefined_keys = []

        conf_prefix = self.CONFIG_PREFIX + '_'

        for key in dir(mod):
            if key.lower().startswith(self.CONFIG_PREFIX.lower()):
                _key = key.replace(conf_prefix, '').lower()
                if _key not in conf.keys():
                    undefined_keys.append((_key, getattr(mod, key)))

        if len(undefined_keys) > 0:
            warnings.warn(
                'Found undefined keys %s in %s '
                'We recommend add these keys into LEONARDO_CONF_SPEC' % (
                    [key for key, val in undefined_keys], mod))

        return undefined_keys

    def extract_conf_from(self, mod, conf, depth=0, max_depth=2):
        """recursively extract keys from module or object
        by passed config scheme or finding all keys
        """

        # extract config keys from module or object
        for key, default_value in conf.items():
            conf[key] = get_key_from_module(
                mod, key, default_value, self.CONFIG_PREFIX)

        # check and update undefined keys
        if self.CHECK_UNDEFINED_KEYS:
            undefined_keys = self._get_undefiend_keys(mod, conf)
            if self.USE_UNDEFINED_KEYS:
                for key in undefined_keys:
                    if key[0] not in self.undefined_keys:
                        self.undefined_keys.append(key)

        # support for recursive dependecies
        try:
            filtered_apps = [
                app for app in conf['apps'] if app not in self.blacklist]
        except TypeError as e:
            raise Exception(conf['apps'])
        except Exception as e:
            raise e
            warnings.warn('Error %s during loading %s' % (e, conf['apps']))

        for app in filtered_apps:

            try:

                app_module = import_module(app)

                if app_module != mod:

                    app_module = self.find_config_module(app_module)

                    if depth < max_depth:

                        if not self.is_leonardo_module(app_module):
                            continue

                        mod_conf = self.extract_conf_from(
                            app_module, conf=self.empty_config,
                            depth=depth + 1)

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

    @property
    def urlpatterns(self):
        '''load and decorate urls from all modules

        This is example how use this loader in Django app

        basically this method is designed to be overwritten, but
        in the default state loads all urlpatterns and decorate it with
        require_auth decorator which can be change using
        '''

        # Django-specific: import django now
        from django.utils.module_loading import module_has_submodule  # noqa
        from django.contrib.auth.decorators import login_required
        from django.conf.urls import include, url

        if hasattr(self, "_urlpatterns"):
            return self._urlpatterns

        urlpatterns = []

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
                                              login_required)
                            urlpatterns += urls_mod.urlpatterns

        # avoid circural dependency
        # TODO use our loaded modules instead this property
        from django.conf import settings
        for urls_conf, conf in getattr(settings, 'MODULE_URLS', {}).items():
            # is public ?
            try:
                if conf['is_public']:
                    urlpatterns += [url(r'', include(urls_conf))]
                else:
                    _decorate_urlconf(
                        url(r'', include(urls_conf)),
                        login_required)
                    urlpatterns += [url(r'', include(urls_conf))]

            except Exception as e:
                raise Exception('raised %s during loading %s' %
                                (str(e), urls_conf))

        self._urlpatterns = urlpatterns
        return self._urlpatterns

    def disable_autoload(self):
        '''Just disable autoloading'''
        self.MODULES_AUTOLOAD = False

    def enable_autoload(self):
        '''Just enable autoloading'''
        self.MODULES_AUTOLOAD = True
