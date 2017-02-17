from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone
from django.db import models

from ct.models import Unit, Course, CourseUnit, Lesson, UnitLesson
from ctms.models import SharedCourse


class MyTestCase(TestCase):
    def setUp(self):
        self.username, self.password = 'test', 'test'
        self.user = User.objects.create_user('test', 'test@test.com', 'test')

        self.user2 = User.objects.create_user('test1', 'test1@test.com', 'test')

        self.unit = Unit(title='Test title', addedBy=self.user)
        self.unit.save()
        self.course = Course(title='Test title',
                             description='test description',
                             access='Public',
                             enrollCode='111',
                             lockout='222',
                             addedBy=self.user)
        self.course.save()

        self.courseunit = CourseUnit(
            unit=self.unit, course=self.course,
            order=0, addedBy=self.user, releaseTime=timezone.now()
        )
        self.courseunit.save()
        self.lesson = Lesson(title='title', text='text', addedBy=self.user)
        self.lesson.save()
        self.unitlesson = UnitLesson(
            unit=self.unit, order=0,
            lesson=self.lesson, addedBy=self.user,
            treeID=self.lesson.id
        )
        self.unitlesson.save()
        self.client.login(username=self.username, password=self.password)
        self.url = reverse('ctms:course_settings', kwargs={'pk': self.course.id})

    def get_page(self):
        return self.client.get(self.url)

    def post_valid_data(self, data={'name': 'some test name'}):
        response = self.client.post(self.url, data)
        return response

    def post_invalid_data(self, data={'name': ''}):
        response = self.client.post(self.url, data)
        return response

    def get_my_courses(self):
        return Course.objects.filter(addedBy=self.user)

    def get_test_course(self):
        return Course.objects.get(id=self.course.id)

    def get_test_unitlessons(self):
        return self.courseunit.unit.unitlesson_set.filter(
            kind=UnitLesson.COMPONENT,
            order__isnull=False
        ).order_by('order').annotate(
            responses_count=models.Count('response')
        )

    def get_test_courseunit(self):
        return CourseUnit.objects.get(id=self.courseunit.id)


class MyCoursesTests(MyTestCase):
    def setUp(self):
        self.username, self.password = 'test', 'test'
        self.user = User.objects.create_user('test', 'test@test.com', 'test')

        self.user2 = User.objects.create_user('test1', 'test1@test.com', 'test')

        self.unit = Unit(title='Test title', addedBy=self.user)
        self.unit.save()
        self.course = Course(title='Test title',
                             description='test description',
                             access='Public',
                             enrollCode='111',
                             lockout='222',
                             addedBy=self.user)
        self.course.save()

        self.courseunit = CourseUnit(
            unit=self.unit, course=self.course,
            order=0, addedBy=self.user, releaseTime=timezone.now()
        )
        self.courseunit.save()
        self.lesson = Lesson(title='title', text='text', addedBy=self.user)
        self.lesson.save()
        self.unitlesson = UnitLesson(
            unit=self.unit, order=0,
            lesson=self.lesson, addedBy=self.user,
            treeID=self.lesson.id
        )
        self.unitlesson.save()
        self.client.login(username=self.username, password=self.password)
        self.url = reverse('ctms:my_courses')

    def get_my_courses_page_test(self):
        response = self.client.get(self.url)
        # should contain 1 course
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ctms/my_courses.html')
        self.assertIn('my_courses', response.context)
        self.assertIn('shared_courses', response.context)
        self.assertIn('course_form', response.context)
        self.assertIn(self.course, response.context['my_courses'])
        self.assertFalse(response.context['shared_courses'])

    def my_courses_show_shared_courses_test(self):
        self.course.addedBy = self.user2
        self.course.save()
        # create shared course
        shared_course = SharedCourse.objects.create(
            from_user=self.user2,
            to_user=self.user,
            course=self.course
        )
        response = self.client.get(self.url)
        # should return shared courses
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ctms/my_courses.html')
        self.assertIn('my_courses', response.context)
        self.assertIn('shared_courses', response.context)
        self.assertIn('course_form', response.context)
        self.assertFalse(self.course in response.context['my_courses'])
        self.assertTrue(shared_course in response.context['shared_courses'])

    def my_courses_show_create_course_form(self):
        self.course.delete()
        response = self.client.get(self.url)
        # should return Course form
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ctms/my_courses.html')
        self.assertIn('my_courses', response.context)
        self.assertIn('shared_courses', response.context)
        self.assertIn('course_form', response.context)
        self.assertFalse(len(response.context['my_courses']) < 0)

    def post_valid_create_course_form(self):
        courses_cnt = Course.objects.filter(addedBy=self.user).count()
        course_ids = [
            i['id'] for i in
            Course.objects.filter(addedBy=self.user).values('id')
        ]
        data = {
            'name': 'some course'
        }
        response = self.client.post(self.url, data)
        new_courses = Course.objects.filter(addedBy=self.user)
        new_course = new_courses.exclude(id__in=course_ids).get()
        self.assertEqual(new_courses.count(), courses_cnt)
        self.assertRedirects(response, reverse('ctms:course_view', kwargs={'course_id': new_course.id}))
        return response

    def post_invalid_create_course_form(self):
        courses_cnt = Course.objects.filter(addedBy=self.user).count()
        course_ids = [
            i['id'] for i in
            Course.objects.filter(addedBy=self.user).values('id')
        ]
        data = {
            'name': ''
        }
        response = self.client.post(self.url, data)
        new_courses = Course.objects.filter(addedBy=self.user)
        new_course = new_courses.exclude(id__in=course_ids)
        self.assertNotEqual(new_courses.count(), courses_cnt)
        # course was not created
        self.assertEqual(len(new_course) == 0)
        self.assertTemplateUsed(response, 'ctms/my_courses.html')
        return response

    def post_valid_create_course_form_to_create_course_view(self):
        self.url = reverse('ctms:create_course')
        self.post_valid_create_course_form()

    def post_invalid_create_course_form_to_create_course_view(self):
        self.url = reverse('ctms:create_course')
        response = self.post_invalid_create_course_form()


class UpdateCourseViewTests(MyTestCase):
    def post_valid_update_course_form(self):
        cnt = self.get_my_courses().count()
        response = self.post_valid_create_course_form()
        # check that courses count doesn't change
        self.assertEqual(cnt, self.get_my_courses().count())
        # check that name has been changed
        self.assertEqual(self.get_test_course().name, 'some test name')
        self.assertRedirects(response, reverse('ctms:course_view', kwargs={'pk': self.course.id}))

    def post_invalid_update_course_form(self):
        cnt = self.get_my_courses().count()
        response = self.post_invalid_data()
        self.assertEqual(cnt, self.get_my_courses().count())
        self.assertEqual(response.context['object'], self.get_test_course())
        self.assertTemplateNotUsed(response, 'ctms/my_courses.html')


class DeleteCourseViewTest(MyTestCase):
    def setUp(self):
        super(DeleteCourseViewTest, self).setUp()
        self.url = reverse('ctms:course_delete', kwargs={'pk': self.course.id})

    def post_success(self):
        cnt = self.get_my_courses().count()
        response = self.client.post(self.url)
        self.assertNotEqual(cnt, self.get_my_courses().count())
        self.assertRedirects(response, reverse('ctms:my_courses'))

    def anonymous_post(self):
        self.client.logout()
        cnt = self.get_my_courses().count()
        response = self.client.post(self.url)
        self.assertEqual(cnt, self.get_my_courses().count())

    def delete_not_mine_course(self):
        self.course.addedBy = self.user2
        self.course.save()
        cnt = self.get_my_courses().count()
        response = self.client.post(self.url)
        self.assertEqual(cnt, self.get_my_courses().count())

    def delete_not_exist_pk_test(self):
        self.url = reverse('ctms:course_delete', kwargs={'pk': 9999999})
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)


class SharedCoursesListViewTests(MyTestCase):
    def setUp(self):
        super(SharedCoursesListViewTests, self).setUp()
        self.shared_course = SharedCourse.objects.create(
            from_user=self.user2,
            to_user=self.user,
            course=self.course
        )
        self.url = reverse('ctms:shared_courses')

    def shared_courses_list_test(self):
        response = self.client.get(self.url)
        self.assertIn(self.shared_course, response.context['shared_courses'])


class CourseViewTests(MyTestCase):
    def setUp(self):
        super(CourseViewTests, self).setUp()
        self.url = reverse('ctms:course_view', kwargs={'pk': self.course.id})

    def course_view_test(self):
        response = self.get_page()
        self.assertEqual(self.course, response.context['object'])
        self.assertEqual(
            self.course.get_course_units(publishedOnly=False),
            response.context['courslets']
        )

    def get_not_mine_course_test(self):
        self.url = reverse('ctms:course_view', kwargs={'pk': 99999})
        response = self.get_page()
        self.assertEqual(response.status_code, 404)

    def logged_out_user_get_course(self):
        self.client.logout()
        response = self.get_page()
        self.assertRedirects(response, reverse('login'))


class CoursletViewTests(MyTestCase):
    def setUp(self):
        super(CoursletViewTests, self).setUp()
        self.url = reverse(
            'ctms:courslet_view',
            kwargs={
                'course_pk': self.course.id,
                'pk': self.courseunit.id

            })

    def get_courslet_view_test(self):
        response = self.get_page()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['u_lessons'], self.get_test_unitlessons())
        self.assertIn(self.unitlesson, response.context['u_lessons'])
        self.assertEqual(self.get_test_courseunit(), response.context['object'])

    def get_courslet_view_wrong_courslet_id_test(self):
        self.url = reverse(
            'ctms:courslet_view',
            kwargs={
                'course_pk': self.course.id,
                'pk': 99999

            })
        response = self.get_page()
        self.assertEqual(response.status_code, 404)

    def get_courslet_view_wrong_course_id_test(self):
        self.url = reverse(
            'ctms:courslet_view',
            kwargs={
                'course_pk': 999999,
                'pk': self.courseunit.id

            })
        response = self.get_page()
        self.assertEqual(response.status_code, 404)

    def get_courslet_view_logged_out_user_test(self):
        self.client.logout()
        response = self.get_page()
        self.assertRedirects(response, reverse('login') + "?next=" + self.url)


class CreateCoursletViewTests(MyTestCase):
    def setUp(self):
        super(CreateCoursletViewTests, self).setUp()
        self.url = reverse(
            'ctms:courslet_create', kwargs={
                'course_pk': self.course.id,
        })

    def post_valid_data_test(self):
        pass

    def post_invalid_data_test(self):
        pass