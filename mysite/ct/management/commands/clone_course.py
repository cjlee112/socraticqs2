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
    help = 'Get report'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('course_id', type=int)

    def handle(self, *args, **options):
        course_id = options['course_id']
        course = Course.objects.filter(id=course_id).first()

        if course:
            title = course.title + " copied {}".format(timezone.now())
            new_course = copy_model_instance(
                course,
                atime=timezone.now(),
                title=title
            )
            for cu in course.courseunit_set.all():
                # deal with Unit
                n_unit = copy_model_instance(cu.unit, atime=timezone.now())
                # deal with CourseUnit
                n_cu = copy_model_instance(cu, course=new_course, unit=n_unit, atime=timezone.now())

                uls = list(cu.unit.get_exercises())
                # copy exercises and error models
                for ul in uls:
                    n_ul = ul.copy(unit=n_unit, addedBy=ul.addedBy)

                # copy resources
                for ul in list(cu.unit.unitlesson_set.filter(kind=UnitLesson.COMPONENT, order__isnull=True)):
                    n_ul = ul.copy(unit=n_unit, addedBy=ul.addedBy)
                    n_unit.reorder_exercise()

            for role in course.role_set.filter(role=Role.INSTRUCTOR):
                n_role = copy_model_instance(role, course=new_course, atime=timezone.now())

            print('Done')
            print('New Course id is {0}'.format(new_course.id))
        else:
            print('There is no Course w/ such id')
