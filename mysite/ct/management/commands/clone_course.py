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
        publish = options['publish']
        with_students = options['with_students']

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
                n_cu_kw = dict(
                    course=new_course,
                    unit=n_unit,
                    atime=timezone.now(),
                )
                if not publish:
                    n_cu_kw['releaseTime'] = None
                n_cu = copy_model_instance(cu, **n_cu_kw)

                uls = list(cu.unit.get_exercises())
                # copy exercises and error models
                for ul in uls:
                    n_ul = ul.copy(unit=n_unit, addedBy=ul.addedBy)

                # copy resources
                for ul in list(cu.unit.unitlesson_set.filter(kind=UnitLesson.COMPONENT, order__isnull=True)):
                    n_ul = ul.copy(unit=n_unit, addedBy=ul.addedBy)
                    n_unit.reorder_exercise()

            roles_to_copy = [Role.INSTRUCTOR] + ([Role.ENROLLED] if with_students else [])
            for role in course.role_set.filter(role__in=roles_to_copy):
                n_role = copy_model_instance(role, course=new_course, atime=timezone.now())
            print('Done')
            print('New Course id is {0}'.format(new_course.id))
        else:
            print('There is no Course w/ such id')
