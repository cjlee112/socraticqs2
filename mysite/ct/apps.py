"""
App's configs.
"""
from django.apps import AppConfig


class CourseletsConfig(AppConfig):

    name = 'ct'
    verbose_name = 'ct'

    def ready(self):
        from . import signals  # noqa
