from django.test import TestCase
from django.utils import timezone
from django.core.management import call_command
from ct.models import Course, CourseUnit, Unit, UnitLesson, Role


class CloneCourseCommandTest(TestCase):
    fixtures = [
        'ct/tests/fixtures/initial_data.json'
    ]

    def get_course_roles(self, course, with_students=False):
        roles_to_copy = [Role.INSTRUCTOR] + ([Role.ENROLLED] if with_students else [])
        return course.role_set.filter(role__in=roles_to_copy)

    def test_call_no_params(self):
        '''
        Tests that copied courselets will be unpublished.
        :return:
        '''
        c = Course.objects.get(id=1)
        # publish all courselets

        cu = c.courseunit_set.all()

        roles_profs = self.get_course_roles(c).values_list('user', flat=True)

        course_ids = set(Course.objects.all().values_list('id', flat=True))

        #########
        call_command('clone_course', '1')
        #########

        new_ids = set(Course.objects.all().values_list('id', flat=True))

        self.assertNotEqual(new_ids, course_ids)

        new_course_id = list(new_ids - course_ids)[0]
        nc = Course.objects.get(id=new_course_id)

        self.assertIn(c.title, nc.title)

        new_roles_profs = self.get_course_roles(nc).values_list('user', flat=True)

        self.assertListEqual(list(new_roles_profs), list(roles_profs))

        ncu = nc.courseunit_set.all()

        self.assertEqual(ncu.count(), cu.count())

        self.assertTrue(all(not i.releaseTime for i in ncu))


    def test_publish(self):
        '''
        If we pass --publish - courseUnit will be copied published
        :return:
        '''
        c = Course.objects.get(id=1)
        # publish all courselets

        cu = c.courseunit_set.all()

        publ_cu = c.courseunit_set.filter(releaseTime__isnull=False).count()
        np_cu = c.courseunit_set.filter(releaseTime__isnull=True).count()

        course_ids = set(Course.objects.all().values_list('id', flat=True))

        #########
        call_command('clone_course', '1', '--publish')
        #########

        new_ids = set(Course.objects.all().values_list('id', flat=True))

        self.assertNotEqual(new_ids, course_ids)
        new_course_id = list(new_ids - course_ids)[0]

        nc = Course.objects.get(id=new_course_id)

        n_publ_cu = nc.courseunit_set.filter(releaseTime__isnull=False).count()
        n_np_cu = nc.courseunit_set.filter(releaseTime__isnull=True).count()

        self.assertIn(c.title, nc.title)

        ncu = nc.courseunit_set.all()

        self.assertEqual(ncu.count(), cu.count())
        self.assertFalse(publ_cu == n_publ_cu)
        self.assertFalse(np_cu == n_np_cu)
        self.assertTrue(publ_cu+np_cu == n_publ_cu)
