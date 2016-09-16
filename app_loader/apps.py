
from django.apps import AppConfig


class Config(AppConfig):
    name = 'app_loader'
    verbose_name = "python-app-loader"

    apps = ['app_loader']
