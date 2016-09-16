

from django.utils import six
from importlib import import_module


def get_key_from_module(mod, key, default, config_prefix):
    '''returns key from object or module

    tries to find key on object likes this::

        my_conf.widgets = ['...']

    and on pythom module::

        LEONARDO_WIDGETS = ['...']

    LEONARDO is config prefix which is configurable from main object
    '''
    if hasattr(mod, key):
        value = getattr(mod, key, default)
    else:
        value = getattr(mod, '%s_%s' % (
            config_prefix.upper(), key.upper()), default)
    return value


CONFIG_VALID = (list, tuple, dict)


def merge(a, b):
    """return merged tuples or lists without duplicates
    note: ensure if admin theme is before admin
    """
    if isinstance(a, CONFIG_VALID) \
            and isinstance(b, CONFIG_VALID):
        # dict update
        if isinstance(a, dict) and isinstance(b, dict):
            a.update(b)
            return a
        # list update
        _a = list(a)
        for x in list(b):
            if x not in _a:
                _a.append(x)
        return _a
    if a and b:
        raise Exception("Cannot merge")
    raise NotImplementedError


def get_object(path, fail_silently=False):
    """Load object for example module.Class"""

    if not isinstance(path, six.string_types):
        return path

    try:
        return import_module(path)
    except ImportError:
        try:
            dot = path.rindex('.')
            mod, fn = path[:dot], path[dot + 1:]

            return getattr(import_module(mod), fn)
        except (AttributeError, ImportError):
            if not fail_silently:
                raise


def _decorate_urlconf(urlpatterns, decorator, *args, **kwargs):
    '''Decorate all urlpatterns by specified decorator'''

    if isinstance(urlpatterns, (list, tuple)):

        for pattern in urlpatterns:
            if getattr(pattern, 'callback', None):
                pattern._callback = decorator(
                    pattern.callback, *args, **kwargs)
            if getattr(pattern, 'url_patterns', []):
                _decorate_urlconf(
                    pattern.url_patterns, decorator, *args, **kwargs)
    else:
        if getattr(urlpatterns, 'callback', None):
            urlpatterns._callback = decorator(
                urlpatterns.callback, *args, **kwargs)
