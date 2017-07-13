from copy import copy

from django.utils import timezone
from django.core.management.base import BaseCommand

from ct.models import Course, Role, UnitLesson
from ct.views import create_error_ul


def copy_model_instance(inst, commit=True, **kwargs):
    n_inst = copy(inst)
    n_inst.id = None
    if kwargs:
        for k, v in kwargs.items():
            setattr(n_inst, k, v)
    if commit:
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
                n_unit = copy_model_instance(cu.unit, atime=timezone.now())
                n_cu = copy_model_instance(cu, course=new_course, unit=n_unit, atime=timezone.now())

                uls = list(cu.unit.unitlesson_set.filter(kind=UnitLesson.COMPONENT))

                for ul in uls:
                    errors = list(ul.get_errors())
                    unit = copy_model_instance(ul.unit)
                    q_lesson = copy_model_instance(ul.lesson)
                    q_ul = copy_model_instance(ul, unit=unit, lesson=q_lesson)

                    n_ul = copy_model_instance(
                        ul,
                        lesson=q_lesson,
                        unit=q_ul.unit,
                        atime=timezone.now()
                    )
                    n_ul.treeID = n_ul.id
                    n_ul.save()

                    for error in errors:
                        # n_concept = copy_model_instance(error.lesson.concept)
                        concept = error.lesson.concept
                        n_lesson = copy_model_instance(error.lesson)
                        n_lesson.save_root(concept)
                        err_ul = UnitLesson.create_from_lesson(n_lesson, unit)
                        emUL1 = create_error_ul(
                            n_lesson,
                            concept,
                            ul.unit,
                            ul
                        )

            for role in course.role_set.filter(role=Role.INSTRUCTOR):
                n_role = copy_model_instance(role, course=new_course, atime=timezone.now())



            print('Done')
            print('New Course id is {0}'.format(new_course.id))
        else:
            print('There is no Course w/ such id')


'''
            for cu in course.courseunit_set.all():
                # deal w ith unit
                n_unit = copy_model_instance(cu.unit, atime=timezone.now())
                # deal with CourseUnit
                n_cu = copy_model_instance(cu, course=new_course, unit=n_unit, atime=timezone.now())

                uls = list(cu.unit.unitlesson_set.filter(parent__isnull=True))  # uls without parent
                # UnitLesson KIND_CHOICES = (
                #     (COMPONENT, 'Included in this courselet'),
                #     (ANSWERS, 'Answer for a question'),
                #     (MISUNDERSTANDS, 'Common error for a question'),
                #     (RESOLVES, 'Resolution for an error'),
                #     (PRETEST_POSTTEST, 'Pre-test/Post-test for this courselet'),
                #     (SUBUNIT, 'Container for this courselet'),
                # )
                # deal with unit lessons which has parent
                nuls_ids = {}  # old_id : (new_id, instance)
                for ul in uls:
                    n_ul = copy_model_instance(ul, unit=n_unit, atime=timezone.now())
                    n_ul.treeID = n_ul.id
                    n_ul.save()
                    nuls_ids[ul.id] = (n_ul.id, n_ul)

                def deep_cp_ul(course, left_to_copy):
                    unit_ids = [i['unit__id'] for i in course.courseunit_set.all().values('unit__id')]
                    for ul in left_to_copy:
                        n_parent = nuls_ids.get(ul.parent.id, [None, None])[1]
                        if ul.parent.unit.id not in unit_ids or n_parent:  # if ul was copied from other unit
                            if ul in left_to_copy:
                                left_to_copy.remove(ul)

                            n_l = copy_model_instance(ul.lesson)
                            n_l.save()

                            if ul.kind == UnitLesson.MISUNDERSTANDS:
                                concept = n_l.concept
                                n_l.save_root(concept)
                                n_ul = UnitLesson.create_from_lesson(n_l, n_ul.unit)
                                em = create_error_ul(
                                    n_l,
                                    concept,
                                    n_ul.unit,
                                    n_ul
                                )
                                n_l.save_as_error_model(ul.concept, n_parent, em)
                            else:
                                n_ul = copy_model_instance(
                                    ul,
                                    lesson=n_l,
                                    unit=n_unit,
                                    atime=timezone.now()
                                )
                                n_ul.treeID = n_ul.id
                                n_ul.parent = n_parent
                                n_ul.save()
                                # add new ul to parents dict
                                nuls_ids[ul.id] = (n_ul.id, n_ul)
                    if left_to_copy:
                        deep_cp_ul(course, left_to_copy)


                uls = list(cu.unit.unitlesson_set.filter(
                    parent__isnull=False,
                ).order_by(
                    '-parent'
                ))
                deep_cp_ul(course, uls)

            for role in course.role_set.filter(role=Role.INSTRUCTOR):
                n_role = copy_model_instance(role, course=new_course, atime=timezone.now())
'''
