

from django.utils import six
from importlib import import_module


def get_key_from_module(mod, key, default):
    if hasattr(mod, key):
        value = getattr(mod, key, default)
    else:
        value = getattr(mod, 'LEONARDO_%s' % key.upper(), default)
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
