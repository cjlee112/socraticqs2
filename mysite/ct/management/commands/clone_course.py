from copy import copy

from django.utils import timezone
from django.core.management.base import BaseCommand

from ct.models import Course, Role, UnitLesson


def copy_model_instance(inst, **kwargs):
    n_inst = copy(inst)
    n_inst.id = None
    if kwargs:
        for k, v in kwargs.items():
            setattr(n_inst, k, v)
    n_inst.save()
    return n_inst


class Command(BaseCommand):
    help = 'Clone course'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('course_id', type=int)
        # Publish\UnPublish courseUnit
        parser.add_argument(
            '--publish',
            action='store_true',
            dest='publish',
            default=False,
            help='Publish cloned course and course units right now? (Default is False - course units will not be published)',
        )
        # Copy student roles
        parser.add_argument(
            '--with-students',
            action='store_true',
            dest='with_students',
            default=False,
            help='Do I need to copy student\'s roles assigned to source course?',
        )


    def handle(self, *args, **options):
        course_id = options['course_id']
        course = Course.objects.filter(id=course_id).first()

        if course:
            new_course = course.deep_clone(**options)
            print('Done')
            print('New Course id is {0}'.format(new_course.id))
        else:
            print('There is no Course w/ such id')
