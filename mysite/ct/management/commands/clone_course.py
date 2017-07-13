from django.utils import timezone
from django.core.management.base import BaseCommand

from ct.models import Course, Role


def copy_model_instance(inst, **kwargs):
    from copy import copy
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
        course_id=options['course_id']
        course = Course.objects.filter(id=course_id).first()

        if course:
            new_course = copy_model_instance(course, atime=timezone.now())
            for cu in course.courseunit_set.all():
                # deal w ith unit
                n_unit = copy_model_instance(cu.unit, atime=timezone.now())
                # deal with CourseUnit
                n_cu = copy_model_instance(cu, course=new_course, unit=n_unit, atime=timezone.now())

                uls = list(cu.unit.unitlesson_set.filter(parent__isnull=True))  # uls without parent

                # deal with unit lessons which has parent
                nuls_ids = {}  # old_id : (new_id, instance)
                for ul in uls:
                    n_ul = copy_model_instance(ul, unit=n_unit, atime=timezone.now())
                    n_ul.treeID = n_ul.id
                    n_ul.save()
                    nuls_ids[ul.id] = (n_ul.id, n_ul)

                def deep_cp_ul(left_to_copy):
                    for ul in left_to_copy:
                        n_parent = nuls_ids.get(ul.parent.id, [None, None])[1]
                        if n_parent:
                            if ul in left_to_copy:
                                left_to_copy.remove(ul)
                            n_ul = copy_model_instance(ul, unit=n_unit, atime=timezone.now())
                            n_ul.treeID = n_ul.id
                            n_ul.parent = n_parent
                            n_ul.save()
                            # add new ul to parents dict
                            nuls_ids[ul.id] = (n_ul.id, n_ul)
                    if left_to_copy:
                        deep_cp_ul(left_to_copy)

                DEEP_LVLS = 3

                for lvl in range(1, DEEP_LVLS + 1):
                    parent_q = '__parent' * lvl
                    uls = list(cu.unit.unitlesson_set.filter(
                        parent__isnull=False,
                        **{'parent' + parent_q + '__isnull': True}
                    ).order_by(
                        '-parent' + parent_q
                    ))
                    deep_cp_ul(uls)

            for role in course.role_set.filter(role=Role.INSTRUCTOR):
                n_role = copy_model_instance(role, course=new_course, atime=timezone.now())

            print('Done')
            print('New Course id is {0}'.format(new_course.id))
        else:
            print('There is no Course w/ such id')