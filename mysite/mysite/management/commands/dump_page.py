from copy import copy
from cms.models.titlemodels import Title
from django.core.management import call_command

from django.utils import timezone
from django.core.management.base import BaseCommand
from cms.models import Page

class Command(BaseCommand):
    help = 'Populate DB with default data'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('--slug', type=str)
        parser.add_argument('--file', type=str)


    def handle(self, *args, **options):
        slug = options['slug']
        print slug

        titles = Title.objects.filter(slug=slug)
        print titles

        pages = []

        for title in titles:
            page = title.page
            pages.append(page)

            for ph in page.placeholders.all():
                import ipdb; ipdb.set_trace()


        '''
        serializers.serialize(format, get_objects(), indent=indent,
                        use_natural_foreign_keys=use_natural_foreign_keys,
                        use_natural_primary_keys=use_natural_primary_keys,
                        stream=stream or self.stdout)
        '''
