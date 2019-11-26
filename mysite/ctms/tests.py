import mock
from unittest import skip

from ddt import ddt, data, unpack
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from django.db import models
from accounts.models import Instructor
from chat.models import EnrollUnitCode

from ct.models import (
    Unit, Course, CourseUnit, Lesson, UnitLesson, Response, NEED_HELP_STATUS, SubKindMixin, Role)
from ctms.forms import EditUnitForm
from ctms.models import Invite
from psa.forms import EmailLoginForm, SignUpForm


@override_settings(SUSPEND_SIGNALS=True)
class MyTestCase(TestCase):
    models_to_check = tuple()
    context_should_contain_keys = tuple()

    def setUp(self):
        self.username, self.password = 'test', 'test'
        self.user = User.objects.create_user(self.username, 'test@test.com', self.password)

        self.instructor = Instructor.objects.create(user=self.user, institution='institute',
                                                    what_do_you_teach='something')

        self.username2, self.password2 = 'test1', 'test'
        self.user2 = User.objects.create_user(self.username2, 'test1@test.com', self.password2)
        self.instructor2 = Instructor.objects.create(user=self.user2, institution='institute',
                                                     what_do_you_teach='something')

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

        self.resp1 = Response(
            unitLesson=self.unitlesson,
            kind=Response.ORCT_RESPONSE,
            lesson=self.lesson,
            course=self.course,
            text="Some text user may respond",
            author=self.user,
            status=NEED_HELP_STATUS,
            selfeval=Response.DIFFERENT
        )
        self.resp1.save()

        self.resp2 = Response(
            unitLesson=self.unitlesson,
            kind=Response.ORCT_RESPONSE,
            lesson=self.lesson,
            course=self.course,
            text="Some text user may be responded 2",
            author=self.user,
            status=NEED_HELP_STATUS,
            selfeval=Response.DIFFERENT
        )
        self.resp2.save()
        self.default_data = {}

        self.client.login(username=self.username, password=self.password)
        self.url = reverse('ctms:course_settings', kwargs={'pk': self.course.id})

    def get_page(self):
        return self.client.get(self.url)

    def post_data(self, data={'name': 'some test name'}):
        response = self.client.post(self.url, data, follow=True)
        return response

    def get_client_method(self, method='post'):
        client_method = getattr(self.client, method)
        if not client_method:
            raise KeyError('self.client has no property {}'.format(method))
        return client_method

    def post_valid_data(self, data={'name': 'some test name'}, method='post'):
        client_method = self.get_client_method(method)
        copied_data = {}
        if getattr(self, 'default_data', False):
            copied_data.update(self.default_data)
            copied_data.update(data)
        response = client_method(self.url, copied_data, follow=True)
        return response

    def post_invalid_data(self, data={'name': ''}, method='post'):
        client_method = self.get_client_method(method)
        copied_data = {}
        if getattr(self, 'default_data', False):
            copied_data.update(self.default_data)
            copied_data.update(data)
        response = client_method(self.url, copied_data, follow=True)
        return response

    def get_my_courses(self):
        return Course.objects.filter(
            models.Q(addedBy=self.user) |
            models.Q(role__role=Role.INSTRUCTOR, role__user=self.user)
        )

    def get_test_course(self):
        return Course.objects.get(id=self.course.id)

    def get_test_unitlessons(self):
        return self.courseunit.unit.unitlesson_set.filter(
            kind=UnitLesson.COMPONENT,
            order__isnull=False
        ).order_by('order').annotate(
            responses_count=models.Count('response')
        )

    def get_test_unitlesson(self):
        return self.courseunit.unit.unitlesson_set.filter(
            kind=UnitLesson.COMPONENT,
            order__isnull=False
        ).order_by('order').annotate(
            responses_count=models.Count('response')
        )[0]

    get_test_courslet = get_test_unitlesson

    get_test_response = lambda self: self.get_test_responses()[0]

    def get_test_courseunit(self):
        return CourseUnit.objects.get(id=self.courseunit.id)

    def get_test_responses(self):
        return Response.objects.filter(
            unitLesson=self.unitlesson,
            kind=Response.ORCT_RESPONSE,
            lesson=self.lesson,
            course=self.course,
        )

    def get_model_counts(self, **kwargs):
        if isinstance(self.models_to_check, (list, tuple)):
            return {model: model.objects.filter().count() for model in self.models_to_check}
        return {self.models_to_check: self.models_to_check.objects.filter().count()}

    def validate_model_counts(self, first_counts, second_counts, must_equal=False):
        if isinstance(self.models_to_check, (list, tuple)):
            all_models = self.models_to_check
        else:
            all_models = [self.models_to_check]

        for model in all_models:
            if must_equal:
                self.assertEqual(
                    first_counts[model], second_counts[model],
                    "{} ({}) != {} ({}), with must_equal={}".format(
                        model, first_counts[model], model, second_counts[model], must_equal
                    )
                )
            else:
                self.assertNotEqual(
                    first_counts[model], second_counts[model],
                    "{} ({}) == {} ({}), with must_equal={}".format(
                        model, first_counts[model], model, second_counts[model], must_equal
                    )
                )

    def check_context_keys(self, response):
        for key in self.context_should_contain_keys:
            self.assertIn(key, response.context)

    def am_i_instructor(self, method='GET'):
        methods_map = {'GET', self.client.get, 'POST', self.client.post}
        client_method = methods_map.get(method)
        self.assertIsNotNone(client_method)

        if getattr(self, 'url'):
            if getattr(self, 'NEED_INSTRUCTOR'):
                response = client_method(self.url)
                if getattr(self, 'instructor'):
                    self.assertEqual(response.status_code, 200)
                    self.instructor.delete()
                    response = client_method(self.url)
                    self.assertEqual(response.status_code, 403)
                else:
                    self.assertEqual(response.status_code, 403)
            else:
                response = client_method(self.url)
                self.assertEqual(response.status_code, 200)


class OnboardingTests(MyTestCase):

    def setUp(self):
        super(OnboardingTests, self).setUp()
        self.enroll_unit_code = EnrollUnitCode.get_code(self.courseunit)
        self.url = reverse('ctms:onboarding')

    @mock.patch('ctms.views.get_onboarding_setting')
    @mock.patch('ctms.views.settings')
    @mock.patch('ctms.views.waffle')
    def test_onboarding(self, waffle_mock, settings_mock, get_onboarding_setting):
        waffle_mock.switch_is_active.return_value = True
        settings_mock.ONBOARDING_INTRODUCTION_COURSELET_ID = self.courseunit.id
        get_onboarding_setting.return_value = self.course.id
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['enroll_url'], '/chat/enrollcode/' + self.enroll_unit_code)
        self.assertEqual(response.context['introduction_course'], self.course)
        self.assertEqual(response.context['users_course'], self.course)
        self.assertEqual(response.context['users_courselet'], self.courseunit)
        self.assertEqual(response.context['users_thread'], None)
        self.assertEqual(response.status_code, 200)
        #for non - existent courselet, course
        settings_mock.ONBOARDING_INTRODUCTION_COURSELET_ID = 999
        get_onboarding_setting.return_value = 999
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['introduction_course'], None)
        self.assertEqual(response.context['enroll_url'], '#')


@ddt
class MyCoursesTests(MyTestCase):
    def setUp(self):
        self.username, self.password = 'test', 'test'
        self.user = User.objects.create_user('test', 'test@test.com', 'test')
        self.instructor = Instructor.objects.create(user=self.user, institution='institute',
                                                    what_do_you_teach='something')

        self.user2 = User.objects.create_user('test1', 'test1@test.com', 'test')
        self.instructor2 = Instructor.objects.create(user=self.user2, institution='institution',
                                                     what_do_you_teach='something')

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

    def test_get_my_courses_page(self):
        response = self.client.get(self.url)
        # should contain 1 course
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ctms/my_courses.html')
        self.assertIn('my_courses', response.context)
        self.assertIn(self.course, response.context['my_courses'])
    
    def test_get_my_courses_page_instructor_role(self):
        """
        Ensure Role.INSTRUCTOR granted access to a Course.
        """
        course = Course(title='Instructor2 Course',
                             description='test description',
                             access='Public',
                             enrollCode='111',
                             lockout='222',
                             addedBy=self.user2)
        course.save()
        Role.objects.create(role=Role.INSTRUCTOR, course=course, user=self.user)
        response = self.client.get(self.url)
        # should contain 2 courses
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ctms/my_courses.html')
        self.assertIn('my_courses', response.context)
        self.assertIn(self.course, response.context['my_courses'])
        self.assertIn(course, response.context['my_courses'])
        self.assertEqual(len(response.context['my_courses']), 2)

    @data(Role.TA, Role.SELFSTUDY, Role.ENROLLED)
    def test_get_my_courses_page_notinstructor_role(self, role):
        """
        Ensure Role.INSTRUCTOR granted access to a Course.
        """
        course = Course(title='Instructor2 Course',
                                description='test description',
                                access='Public',
                                enrollCode='111',
                                lockout='222',
                                addedBy=self.user2)
        course.save()
        Role.objects.create(role=role, course=course, user=self.user)
        response = self.client.get(self.url)
        # should contain 1 courses
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ctms/my_courses.html')
        self.assertIn('my_courses', response.context)
        self.assertIn(self.course, response.context['my_courses'])
        self.assertNotIn(course, response.context['my_courses'])
        self.assertEqual(len(response.context['my_courses']), 1)

    def test_my_courses_show_shared_courses(self):
        self.course.addedBy = self.user2
        self.course.save()
        # create shared course
        enroll_unit_code = EnrollUnitCode.get_code(self.courseunit, give_instance=True)
        shared_course = Invite.create_new(
            True, self.course, self.instructor2, self.user.email, 'tester', enroll_unit_code)
        response = self.client.get(reverse('ctms:shared_courses'))
        # should return shared courses
        self.assertIn('shared_courses', response.context)
        self.assertNotEqual(len(response.context['shared_courses']), 0)
        self.assertTrue(shared_course.course.title in response.context['shared_courses'])

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
            Course.obget_courslet_view_logged_out_user_testjects.filter(addedBy=self.user).values('id')
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
        self.post_invalid_create_course_form()


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
        response = self.client.delete(self.url)
        self.assertNotEqual(cnt, self.get_my_courses().count())
        self.assertRedirects(response, reverse('ctms:my_courses'))

    def anonymous_post(self):
        self.client.logout()
        cnt = self.get_my_courses().count()
        self.client.post(self.url)
        self.assertEqual(cnt, self.get_my_courses().count())

    def delete_not_mine_course(self):
        self.course.addedBy = self.user2
        self.course.save()
        cnt = self.get_my_courses().count()
        self.client.delete(self.url)
        self.assertEqual(cnt, self.get_my_courses().count())

    def test_delete_not_exist_pk(self):
        self.url = reverse('ctms:course_delete', kwargs={'pk': 9999999})
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 404)


class SharedCoursesListViewTests(MyTestCase):
    def setUp(self):
        super(SharedCoursesListViewTests, self).setUp()
        self.unit2 = Unit(title='Test title2', addedBy=self.user)
        self.unit2.save()

        self.course2 = Course(title='Test title2',
                              description='test description2',
                              access='Public2',
                              enrollCode='1112',
                              lockout='1222',
                              addedBy=self.user)
        self.course2.save()

        self.courseunit2 = CourseUnit(
            unit=self.unit2, course=self.course,
            order=0, addedBy=self.user, releaseTime=timezone.now()
        )
        self.courseunit2.save()

        self.courseunit3 = CourseUnit(
            unit=self.unit, course=self.course2,
            order=0, addedBy=self.user, releaseTime=timezone.now()
        )
        self.courseunit3.save()

        enroll_unit_code = EnrollUnitCode.get_code(self.courseunit, give_instance=True)
        enroll_unit_code2 = EnrollUnitCode.get_code(self.courseunit2, give_instance=True)
        enroll_unit_code3 = EnrollUnitCode.get_code(self.courseunit3, give_instance=True)
        self.tester_shared_course = Invite.create_new(
            invite_type='tester',
            commit=True,
            instructor=self.instructor2,
            email=self.user.email,
            course=self.course,
            enroll_unit_code=enroll_unit_code
        )
        self.tester_shared_course2 = Invite.create_new(
            invite_type='tester',
            commit=True,
            instructor=self.instructor2,
            email=self.user.email,
            course=self.course,
            enroll_unit_code=enroll_unit_code2
        )
        self.tester_shared_course3 = Invite.create_new(
            invite_type='tester',
            commit=True,
            instructor=self.instructor2,
            email=self.user.email,
            course=self.course2,
            enroll_unit_code=enroll_unit_code3
        )
        self.url = reverse('ctms:shared_courses')

    def get_invite_by_id(self, id):
        return Invite.objects.get(id=id)

    def test_shared_courses_list(self):
        response = self.client.get(self.url)

        self.assertEqual(
            reverse('ctms:shared_courses'),
            response.context['shared_courses'][self.course.title]['link']
        )
        self.assertEqual(
            reverse('ctms:tester_join_course', kwargs={'code': self.tester_shared_course3.code}),
            response.context['shared_courses'][self.course2.title]['link']
        )



    def test_join_course(self):
        url = reverse('ctms:tester_join_course', kwargs={'code': self.tester_shared_course.code})
        response = self.client.get(url)
        self.assertRedirects(
            response,
            reverse('chat:tester_chat_enroll', kwargs={'enroll_key': self.tester_shared_course.enroll_unit_code.enrollCode})
        )
        invite = self.get_invite_by_id(self.tester_shared_course.id)
        self.assertEqual(invite.status, 'joined')
        self.join_course_cases(url, self.tester_shared_course)

    def join_course_cases(self, url, invite):
        # if invited user is already registered but not logged in - login form must be shown
        self.client.logout()
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertTrue(isinstance(response.context['form'], EmailLoginForm))
        self.assertEqual(response.context['form'].initial['email'], invite.email)
        self.assertIn('u_hash', response.context['form'].initial)

        # if no such user
        invite.email = 'asdasd@aac.cc'
        invite.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertTrue(isinstance(response.context['form'], SignUpForm))
        self.assertEqual(response.context['form'].initial['email'], invite.email)
        self.assertIn('u_hash', response.context['form'].initial)

        # if user registered after sending invitation - login form must be shown
        User.objects.create_user('asdasd', 'asdasd@aac.cc', '123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertTrue(isinstance(response.context['form'], EmailLoginForm))
        self.assertEqual(response.context['form'].initial['email'], invite.email)
        self.assertIn('u_hash', response.context['form'].initial)

    def student_join_course(self):
        url = reverse('ctms:tester_join_course', kwargs={'code': self.student_shared_course.code})

        response = self.client.get(url)
        self.assertRedirects(
            response,
            reverse('lms:course_view', kwargs={'course_id': self.student_shared_course.course.id})
        )

        invite = self.get_invite_by_id(self.tester_shared_course.id)
        self.assertEqual(invite.status, 'joined')

        self.join_course_cases(url, self.student_shared_course)


class CourseViewTests(MyTestCase):
    def setUp(self):
        super(CourseViewTests, self).setUp()
        self.url = reverse('ctms:course_view', kwargs={'pk': self.course.id})

    def test_course_view(self):
        response = self.get_page()
        self.assertEqual(self.course, response.context['object'])
        self.assertEqual(
            self.course.get_course_units(publishedOnly=False),
            response.context['courslets']
        )

    def test_get_not_mine_course(self):
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

    def test_get_courslet_view(self):
        response = self.get_page()
        self.assertEqual(response.status_code, 200)
        u_ids = [i['id'] for i in response.context['u_lessons'].values('id')]
        test_ids = [i['id'] for i in self.get_test_unitlessons().values('id')]
        self.assertEqual(u_ids, test_ids)
        self.assertIn(self.unitlesson, response.context['u_lessons'])
        self.assertEqual(self.get_test_courseunit(), response.context['object'])

    def test_get_courslet_view_wrong_courslet_id(self):
        self.url = reverse(
            'ctms:courslet_view',
            kwargs={
                'course_pk': self.course.id,
                'pk': 99999

            })
        response = self.get_page()
        self.assertEqual(response.status_code, 404)

    def test_get_courslet_view_wrong_course_id(self):
        self.url = reverse(
            'ctms:courslet_view',
            kwargs={
                'course_pk': 999999,
                'pk': self.courseunit.id

            })
        response = self.get_page()
        self.assertEqual(response.status_code, 404)

    def test_get_courslet_view_logged_out_user(self):
        self.client.logout()
        response = self.get_page()
        self.assertRedirects(response, reverse('new_login') + "?next=" + self.url)


class CreateCoursletViewTests(MyTestCase):
    def setUp(self):
        super(CreateCoursletViewTests, self).setUp()
        self.default_data = {}
        self.url = reverse(
            'ctms:courslet_create', kwargs={
                'course_pk': self.course.id,
        })

    def test_invalid_get_create_courselet_view(self):
        self.url = reverse(
            'ctms:courslet_create', kwargs={
                'course_pk': 9999,
        })
        response = self.get_page()
        self.assertEqual(response.status_code, 404)

    def test_post_valid_data(self):
        courslets_in_course = CourseUnit.objects.filter(
            course=self.course
        ).count()
        data = {
            'title': 'Some new Courslet',
            'graded_assessment_datetime': '2019-01-01',
            'exam_name': 'Exam name'
        }
        response = self.client.post(self.url, data, follow=False)
        new_unit = CourseUnit.objects.filter(
            course=self.course
        ).count()
        self.assertNotEqual(courslets_in_course, new_unit)
        self.assertRedirects(response, reverse(
            'ctms:courselet_best_practice',
            kwargs={
                'course_pk': self.get_test_course().pk,
                'courselet_pk': CourseUnit.objects.all().last().id
            }
        ))

    def test_post_invalid_data(self):
        courslets_in_course = Unit.objects.filter(
            courseunit__course=self.course
        )
        data = {'title': ''}
        response = self.post_invalid_data(data)
        self.assertNotEqual(
            courslets_in_course,
            Unit.objects.filter(courseunit__course=self.course)
        )
        self.assertTemplateUsed('ctms/create_unit_form.html')
        self.assertIn('form', response.context)
        self.assertIn('unit_lesson', response.context)
        self.assertIn('course', response.context)
        self.assertIn('courslet', response.context)


class UnitViewTests(MyTestCase):
    def test_get_page(self):
        self.url = reverse(
            'ctms:unit_view', kwargs={
                'course_pk': self.course.id,
                'courselet_pk': self.courseunit.id,
                'pk': self.unitlesson.id
            }
        )
        response = self.get_page()
        self.assertIn('course', response.context)
        self.assertIn('courslet', response.context)
        self.assertIn('responses', response.context)
        self.assertEqual(response.context['course'], self.course)
        self.assertEqual(response.context['courslet'], self.courseunit)
        self.assertEqual(
            list(response.context['responses'].order_by('id')),
            list(self.get_test_responses().order_by('id')),
        )

    def test_invalid_unit_view(self):
        self.url = reverse(
            'ctms:unit_view', kwargs={
                'course_pk': 99999,
                'courselet_pk': 999,
                'pk': 999
            }
        )
        response = self.get_page()
        self.assertEqual(response.status_code, 404)


class CreateUnitViewTests(MyTestCase):
    def setUp(self):
        super(CreateUnitViewTests, self).setUp()
        self.url = reverse(
            'ctms:unit_create',
            kwargs={
                'course_pk': self.course.id,
                'courselet_pk': self.courseunit.id,

            }
        )
        self.default_data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-id': '',
            'form-0-title': '',
            'form-0-text': '',
        }

    def test_invalid_unit_create(self):
        self.url = reverse(
            'ctms:unit_create',
            kwargs={
                'course_pk': 999,
                'courselet_pk': 999,
            }
        )
        response = self.get_page()
        self.assertEqual(response.status_code, 404)

    def test_get_page(self):
        response = self.get_page()
        self.assertIn('course', response.context)
        self.assertIn('courslet', response.context)
        self.assertIn('unit_lesson', response.context)
        self.assertEqual(response.context['course'], self.course)
        self.assertEqual(response.context['courslet'], self.courseunit)
        self.assertIsNone(response.context['unit_lesson'])

    def test_post_valid_data(self):
        data = {
            'title': 'Some new new one title'
        }
        lessons_cnt = Lesson.objects.filter().count()
        unit_lsn_cnt = UnitLesson.objects.filter().count()
        response = self.post_valid_data(data)
        new_lessons_cnt = Lesson.objects.filter().count()
        new_unit_lsn_cnt = UnitLesson.objects.filter().count()
        last_ul = UnitLesson.objects.all().order_by('id').last()
        success_url = reverse(
            'ctms:unit_edit',
            kwargs={
                'course_pk': self.get_test_course().id,
                'courselet_pk': self.get_test_courseunit().id,
                'pk': last_ul.id
            })
        assert last_ul.lesson.kind == Lesson.ORCT_QUESTION
        self.assertRedirects(response, success_url)
        self.assertNotEqual(lessons_cnt, new_lessons_cnt)
        self.assertNotEqual(unit_lsn_cnt, new_unit_lsn_cnt)

    def test_invalid_unit_edit(self):
        self.url = reverse(
            'ctms:unit_edit', kwargs={
                'course_pk': 99999,
                'courselet_pk': 999,
                'pk': 999
            }
        )
        response = self.get_page()
        self.assertEqual(response.status_code, 404)

    def test_post_invalid_data(self):
        data = {
            'title': ''
        }
        lessons_cnt = Lesson.objects.filter().count()
        unit_lsn_cnt = UnitLesson.objects.filter().count()
        response = self.post_valid_data(data)
        self.assertTemplateUsed('ctms/create_unit_form.html')
        self.assertIn('course', response.context)
        self.assertIn('courslet', response.context)
        self.assertIn('form', response.context)
        self.assertIsNone(response.context['unit_lesson'])
        self.assertEqual(lessons_cnt, Lesson.objects.filter().count())
        self.assertEqual(unit_lsn_cnt, UnitLesson.objects.filter().count())


@ddt
class EditUnitViewTests(MyTestCase):

    models_to_check = (UnitLesson, Lesson)
    context_should_contain_keys = ('unit', 'course', 'courslet')

    def setUp(self):
        super(EditUnitViewTests, self).setUp()
        # need to create user with username 'admin'
        User.objects.create_user(
            username='admin'
        )
        self.pk = self.get_test_unitlessons()[0].id
        self.url = reverse(
            'ctms:unit_edit',
            kwargs={
                'course_pk': self.get_test_course().id,
                'courselet_pk': self.get_test_courseunit().id,
                'pk': self.get_test_unitlessons()[0].id,
            }
        )
        self.default_data = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-0-id': '',
            'form-0-title': '',
            'form-0-text': '',
        }

        # creating the new Lessons of kind 'answer' to avoid redirecting to the Get Started page
        lesson = Lesson(title='title', text='text', addedBy=self.user, kind=Lesson.ANSWER)
        lesson2 = Lesson(title='title', text='text', addedBy=self.user, kind=Lesson.ANSWER)
        lesson.save()
        lesson2.save()

    @data(
        SubKindMixin.MULTIPLE_CHOICES,
        SubKindMixin.NUMBERS,
        SubKindMixin.EQUATION,
        SubKindMixin.CANVAS,
    )
    def test_lesson_type_introduction_sub_kind_MC(self, sub_kind):
        self.lesson.kind=Lesson.ORCT_QUESTION
        self.lesson.sub_kind=sub_kind
        self.lesson.save()

        lesson_id = self.lesson.id
        lesson = Lesson.objects.get(id=lesson_id)

        self.assertEqual(lesson.kind, Lesson.ORCT_QUESTION)
        self.assertEqual(lesson.text, 'text')
        self.assertEqual(lesson.sub_kind, sub_kind)

        self.url = reverse(
            'ctms:unit_edit',
            kwargs={
                'course_pk': self.get_test_course().id,
                'courselet_pk': self.get_test_courseunit().id,
                'pk': lesson_id,
            }
        )
        data = {
            'unit_type': Lesson.EXPLANATION,
            'text': 'text',
            'title': 'title',
        }

        response = self.post_valid_data(data)
        lesson = Lesson.objects.get(id=lesson_id)

        self.assertEqual(lesson.text, 'text')
        self.assertEqual(lesson.kind, Lesson.EXPLANATION)
        self.assertEqual(lesson.title, 'title')
        self.assertEqual(lesson.sub_kind, None)


    def test_get_page(self):
        counts = self.get_model_counts()
        response = self.get_page()
        new_counts = self.get_model_counts()
        self.assertEqual(counts, new_counts)
        self.assertTemplateUsed(response, 'ctms/unit_edit.html')
        self.check_context_keys(response)

    @unpack
    @data(
        (EditUnitForm.KIND_CHOICES[1][0], 'Some text is here...', 'Some new title', 'tests/files/raccoon.jpg'),
        (EditUnitForm.KIND_CHOICES[0][0], 'Some New ORCT text is here...', 'Some ORCT title', 'tests/files/image.svg', 'ORCT Answer'),
        (EditUnitForm.KIND_CHOICES[0][0], 'Some New ORCT text w/o image', 'Some ORCT title w/o image', '', 'ORCT Answer'),
    )
    def test_post_valid_data(self, kind, text, title, attachment, answer=''):
        counts = self.get_model_counts()
        data = {
            'unit_type': kind,
            'text': text,
            'title': title,
            'answer_form-answer': answer,
        }
        if attachment:
            with open(attachment, 'rb') as img:
                data.update({
                    'attachment': img
                })
                response = self.post_valid_data(data)
        else:
            response = self.post_valid_data(data)

        self.assertEqual(response.context['form'].errors, {})
        self.assertEqual(response.context['answer_form'].errors, {})
        self.assertEqual(response.context['errors_formset'].errors, [])

        new_counts = self.get_model_counts()

        if kind == EditUnitForm.KIND_CHOICES[0][0]:  # ORCT
            # must not be equal because we added Answer
            self.validate_model_counts(counts, new_counts, must_equal=False)
        else:
            self.validate_model_counts(counts, new_counts,
                                       must_equal=True)  # must not be equal because we added Answer
        ul = self.get_test_unitlesson()
        url = reverse('ctms:unit_edit', kwargs={
            'course_pk': self.get_test_course().id,
            'courselet_pk': self.get_test_courseunit().id,
            'pk': ul.id
        })
        self.assertEqual(self.get_test_unitlesson().lesson.text, text)
        self.assertEqual(self.get_test_unitlesson().lesson.kind, kind)
        self.assertEqual(self.get_test_unitlesson().lesson.title, title)
        self.assertRedirects(response, url)
        self.check_context_keys(response)

    @unpack
    @data(
        # (EditUnitForm.KIND_CHOICES[0][0], ''),  # valid kind, empty text
        ('', 'Some New ORCT text is here...', 'Some titile', 'tests/files/document.pdf'),  # not valid kind, valid text
        (EditUnitForm.KIND_CHOICES[0][0], 'Some New ORCT text is here...', '', 'pytest.ini'),  # valid kind, not valid title
        (EditUnitForm.KIND_CHOICES[0][0], '', 'Some text', 'tests/files/raccoon3.mp3'),  # valid kind, not valid title
        (EditUnitForm.KIND_CHOICES[0][0], '', '', 'tests/files/raccoon3.mpeg'),  # valid kind, not valid title and text
    )
    def test_post_invalid_data(self, kind, text, title, attachment):
        counts = self.get_model_counts()
        data = {
            'unit_type': kind,
            'text': text,
            'title': title
        }
        if attachment:
            with open(attachment, 'rb') as img:
                data.update({
                    'attachment': img
                })
                response = self.post_valid_data(data)
        else:
            response = self.post_valid_data(data)
        new_counts = self.get_model_counts()
        self.validate_model_counts(counts, new_counts, must_equal=True)
        self.assertEqual(
            [_ for _ in response.context['form'].errors.get('attachment')],
            ['Upload a valid image. The file you uploaded was either not an image or a corrupted image.'])
        self.assertNotEqual(self.get_test_unitlesson().lesson.kind, kind)
        # self.assertEqual(self.get_test_unitlesson().unit.text, text)
        self.check_context_keys(response)

    @unpack
    @data(
        (EditUnitForm.KIND_CHOICES[0][0], 'Some text is here...', 'Some new title', 'Text', 'EM title', 'EM text'),
        (EditUnitForm.KIND_CHOICES[0][0], 'Some New ORCT text is here...', 'Some ORCT title', 'ORCT Answer',
         'EM title', 'EM text'),
    )
    def test_create_error_model(self, kind, title, text, answer, em_title, em_text):
        counts = self.get_model_counts()
        data = self.default_data.copy()
        data['form-0-title'] = em_title
        data['form-0-text'] = em_text
        data.update(
            {
                'form-TOTAL_FORMS': 1,
                'unit_type': kind,
                'text': text,
                'title': title,
                'answer_form-answer': answer,
            }
        )
        response = self.post_valid_data(data)
        self.assertRedirects(response, self.url)
        new_counts = self.get_model_counts()
        self.validate_model_counts(counts, new_counts, must_equal=False)  # must not be equal because we added EM
        # check that 1 error model is present
        self.assertIsNotNone(UnitLesson.objects.filter(kind=UnitLesson.MISUNDERSTANDS).first())
        self.assertEqual(response.context['errors_formset'].errors, [])

    @unpack
    @data(
        (EditUnitForm.KIND_CHOICES[0][0], 'Some text is here...', 'Some new title', 'Text', '', 'EM text'),
        (EditUnitForm.KIND_CHOICES[0][0], 'Some New ORCT text is here...', 'Some ORCT title', 'ORCT Answer', 'EM title',
         ''),
    )
    def test_create_error_model_negative(self, kind, title, text, answer, em_title, em_text):
        counts = self.get_model_counts()
        data = self.default_data.copy()
        data['form-0-title'] = em_title
        data['form-0-text'] = em_text
        data.update(
            {
                'form-TOTAL_FORMS': 1,
                'unit_type': kind,
                'text': text,
                'title': title,
                'answer_form-answer': answer,
            }
        )
        # add answer (with no correct EM, so EM will not be added)
        response = self.post_valid_data(data)
        self.assertEqual(response.status_code, 200)
        # check that formset show error
        self.assertNotEqual(response.context['errors_formset'].errors, [])
        new_counts = self.get_model_counts()
        self.validate_model_counts(counts, new_counts, must_equal=False)  # must be not equal

        # add ErrModel
        counts = self.get_model_counts()
        response = self.post_valid_data(data)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.context['errors_formset'].errors, [])
        new_counts = self.get_model_counts()
        self.validate_model_counts(counts, new_counts, must_equal=True)  # must be equal
        # check that no error models are present
        self.assertIsNone(UnitLesson.objects.filter(kind=UnitLesson.MISUNDERSTANDS).first())

    @skip
    @unpack
    @data(
        (EditUnitForm.KIND_CHOICES[1][0], 'Some text is here...', 'Some new title', 'Text', 'EM title', 'EM text'),
    )
    def test_delete_error_mode_delete_only_ul(self, kind, title, text, answer, em_title, em_text):
        """Test that when delete error model it delete only UnitLesson and not Lesson objects."""
        # create error model
        data = self.default_data.copy()
        data.update(
            {
                'form-TOTAL_FORMS': 1,
                'unit_type': kind,
                'text': text,
                'title': title,
                'answer_form-answer': answer,
                'form-0-title': em_title,
                'form-0-text': em_text,
            }
        )

        response = self.post_valid_data(data)

        # delete this error model
        ul = UnitLesson.objects.filter(kind=UnitLesson.MISUNDERSTANDS).first()

        self.assertIsNotNone(ul)
        data.update({
            'form-0-DELETE': 'on',
            'form-0-id': ul.lesson.id,
            'form-0-ul_id': ul.id,
        })
        counts_n = self.get_model_counts()
        response = self.post_valid_data(data)

        self.assertRedirects(response, self.url)
        new_counts = self.get_model_counts()

        self.validate_model_counts(counts_n, new_counts, must_equal=False)
        self.assertIsNone(UnitLesson.objects.filter(kind=UnitLesson.MISUNDERSTANDS, id=ul.id).first())
        self.assertIsNotNone(Lesson.objects.filter(id=ul.lesson.id).first())


class ResponseViewTests(MyTestCase):
    models_to_check = (Response,)
    context_should_contain_keys = ('course_pk', 'courselet_pk', 'unit_pk', 'pk', 'object')

    def setUp(self):
        super(ResponseViewTests, self).setUp()
        self.url = reverse(
            'ctms:response_view',
            kwargs={
                'course_pk': self.get_test_course().id,
                'courselet_pk': self.get_test_courseunit().id,
                'unit_pk': self.get_test_unitlesson().id,
                'pk': self.get_test_response().id
            }
        )

    def test_get_page(self):
        response = self.get_page()
        self.check_context_keys(response)


@ddt
class CoursletSettingsViewTests(MyTestCase):
    models_to_check = Unit
    context_should_contain_keys = ('course', 'courslet', 'form')

    def setUp(self):
        super(CoursletSettingsViewTests, self).setUp()
        self.kwargs = {
            'course_pk': self.get_test_course().id,
            'pk': self.get_test_courseunit().id
        }
        self.url = reverse(
            'ctms:courslet_settings',
            kwargs=self.kwargs
        )
        self.default_data = {}

    def test_get_page(self):
        response = self.get_page()
        self.check_context_keys(response)

    @unpack
    @data(
        (True, {'title': 'SOme 111 titlee'}),
        (False, {'title': ''})
    )
    def test_post_data(self, is_valid, post_data):
        counts = self.get_model_counts()
        response = self.client.post(self.url, post_data, follow=False)
        new_counts = self.get_model_counts()
        self.validate_model_counts(counts, new_counts, True)

        if is_valid and response.status_code == 200:
            print((response.context['form'].errors))

        if is_valid:
            url = reverse('ctms:courselet_invite_student', kwargs={'pk': self.kwargs['course_pk'],
                                                                   'courselet_pk': self.kwargs['pk']})
            self.assertRedirects(response, url)
            response = self.client.post(self.url, post_data, follow=True)
            self.context_should_contain_keys = ('invite_tester_form', 'courselet', 'course')

        self.check_context_keys(response)


class CoursletDeleteViewTests(MyTestCase):
    context_should_contain_keys = ('course', 'courslet')
    models_to_check = CourseUnit

    def setUp(self):
        super(CoursletDeleteViewTests, self).setUp()
        self.kwargs = {
            'course_pk': self.get_test_course().id,
            'pk': self.get_test_courslet().id
        }
        self.url = reverse('ctms:courslet_delete', kwargs=self.kwargs)

    def test_get_page(self):
        # should return delete confirmation page
        counts = self.get_model_counts()
        response = self.get_page()
        new_counts = self.get_model_counts()
        self.validate_model_counts(counts, new_counts, must_equal=True)
        # self.assertTemplateUsed(response, 'ctms/courselet_confirm_delete.html')

    def test_post_page(self):
        counts = self.get_model_counts()
        response = self.post_valid_data(data=None, method='delete')
        new_counts = self.get_model_counts()
        self.validate_model_counts(counts, new_counts)
        self.assertEqual(counts[self.models_to_check], new_counts[self.models_to_check] + 1)
        self.assertRedirects(
            response,
            reverse('ctms:course_view', kwargs={'pk': self.get_test_course().id})
        )


class DeleteUnitViewTests(MyTestCase):
    context_should_contain_keys = ()
    models_to_check = UnitLesson

    def setUp(self):
        super(DeleteUnitViewTests, self).setUp()
        self.kwargs = {
            'course_pk': self.get_test_course().id,
            'courselet_pk': self.get_test_courseunit().id,
            'pk': self.get_test_courslet().id
        }
        self.url = reverse('ctms:unit_delete', kwargs=self.kwargs)

    def test_delete_unit(self):
        counts = self.get_model_counts()
        response = self.post_valid_data(method='delete')
        new_counts = self.get_model_counts()
        self.validate_model_counts(counts, new_counts)
        url = reverse('ctms:courslet_view',
                      kwargs={
                          'course_pk': self.get_test_course().id,
                          'pk': self.get_test_courseunit().id
                      })
        self.assertRedirects(response, url)


@ddt
class UnitSettingsViewTests(MyTestCase):
    context_should_contain_keys = ('unit_lesson', 'course', 'courslet', 'object')
    models_to_check = UnitLesson

    def setUp(self):
        super(UnitSettingsViewTests, self).setUp()
        self.kwargs = {
            'course_pk': self.get_test_course().id,
            'courselet_pk': self.get_test_courseunit().id,
            'pk': self.get_test_unitlesson().id
        }
        self.url = reverse('ctms:unit_settings', kwargs=self.kwargs)

    def test_get_page(self):
        response = self.get_page()
        self.check_context_keys(response)

    # NOTE: may be we will need this test in future when this page will contain not only links but will update unit.
    # @unpack
    # @data(
    #     (True, {'title': "Some neeewww titleeeeee"}),
    #     (False, {'title': ""})
    # )
    # def test_post_data(self, is_valid, post_data):
    #     counts = self.get_model_counts()
    #     ul = UnitLesson.objects.get(id=self.kwargs['pk'])
    #     response = self.post_data(post_data)
    #     n_ul = UnitLesson.objects.get(id=self.kwargs['pk'])
    #     new_counts = self.get_model_counts()
    #     self.check_context_keys(response)
    #     self.validate_model_counts(counts, new_counts)
    #     if is_valid:
    #         self.assertNotEqual(n_ul.title, ul.title)
    #     else:
    #         self.assertEqual(n_ul.title, ul.title)
