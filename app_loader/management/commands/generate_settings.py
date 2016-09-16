
from __future__ import unicode_literals

import os
import shutil
from optparse import make_option

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, NoArgsCommand
from importlib import import_module


class Command(BaseCommand):

    help = "Generate settings from loaded config module"
    option_list = NoArgsCommand.option_list + (
        make_option('--apps',
                    action='store_false', dest='interactive', default=[],
                    help="Apps for updating as array delimeted with comma."),
    )

    def handle(self, *args, **options):

        self.stdout.write('Successfully pulled')
