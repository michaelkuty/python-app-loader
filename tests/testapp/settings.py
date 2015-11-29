
from app_loader import app_loader

APPS = ['testapp']

# disable autoload
app_loader.disable_autoload()
# load directly specified apps
app_loader.get_app_modules(APPS)

# load all modules
app_loader.load_modules()

# just propagate all loaded modules to settings
LEONARDO_MODULES = app_loader.get_modules()


# override all
try:
    from local_settings import *
except ImportError:
    pass
