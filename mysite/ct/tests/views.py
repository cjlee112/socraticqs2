"""
Unit tests for core app views.py.
"""
from django.test import TestCase
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from mock import Mock, patch
from ddt import ddt, data, unpack

from ct.views import *
from ct.models import UnitLesson, Lesson, Unit
from fsm.fsm_base import FSMStack


@ddt
class MiscTests(TestCase):
    """
    Tests for general functions from views.py.
    """
    @unpack
    @data(
        ('prof', 'assertIsNone'),
        ('student', 'assertIsNotNone'),
        (['prof', 'student'], 'assertIsNone'),
        (['student'], 'assertIsNotNone')
    )
    def test_check_instructor_auth(self, role, check):
        """
        Test positive and negative cases for check_instructor_auth func.
        """
        course = Mock()
        course.get_user_role.return_value = role
        request = Mock()
        result = check_instructor_auth(course, request)
        getattr(self, check)(result)  # Checking returned result for None or for value depending on role
        if check == 'assertIsNotNone':  # If student we need to test 403 Forbidden HttpResponce
            self.assertTrue(isinstance(result, HttpResponse))
            self.assertEqual(result.content, 'Only the instructor can access this')
            self.assertEqual(result.status_code, 403)

    @patch('ct.views.get_base_url')
    @unpack
    @data(
        ('FAQ', [('Resolutions', '/ct/teach/courses/1/units/1/'),
                 ('Resources', '/ct/teach/courses/1/units/1/resources/'),
                 ('FAQ', '#FAQTabDiv')]),
        ('Home', [('Resolutions', '/ct/teach/courses/1/units/1/'),
                  ('Resources', '/ct/teach/courses/1/units/1/resources/'),
                  ('FAQ', '/ct/teach/courses/1/units/1/faq/')])
    )
    def test_make_tabs(self, current, return_list, get_base_url):
        get_base_url.return_value = '/ct/teach/courses/1/units/1/'
        result = make_tabs('/ct/teach/courses/1/units/1/lessons/1/', current, ('Resolutions:', 'Resources', 'FAQ'))
        self.assertEqual(result, return_list)

    @patch('ct.views.make_tabs')
    @unpack
    @data(
        (1, ('Home,Study:', 'Tasks', 'Lessons', 'Concepts', 'Errors', 'FAQ', 'Edit')),
        (None, ('Home,Study:', 'Lessons', 'Concepts', 'Errors', 'FAQ', 'Edit'))
    )
    def test_concept_tabs_teacher_tabs(self, order, tabs, make_tabs):
        unitLesson = Mock()
        unitLesson.order = order
        current = 'FAQ'
        path = '/ct/teach/courses/1/units/1/'
        result = concept_tabs(path, current, unitLesson)
        make_tabs.assert_called_once_with('/ct/teach/courses/1/units/1/', 'FAQ', tabs)
        self.assertEqual(result, make_tabs())

    @patch('ct.views.make_tabs')
    @unpack
    @data(
        (1, ('Study:', 'Tasks', 'Lessons', 'FAQ')),
        (None, ('Study:', 'Lessons', 'FAQ'))
    )
    def test_concept_tabs_student_tabs(self, order, tabs, make_tabs):
        unitLesson = Mock()
        unitLesson.order = order
        current = 'FAQ'
        path = '/ct/courses/1/units/1/'
        result = concept_tabs(path, current, unitLesson)
        make_tabs.assert_called_once_with('/ct/courses/1/units/1/', 'FAQ', tabs)
        self.assertEqual(result, make_tabs())

    @patch('ct.views.is_teacher_url')
    @patch('ct.views.make_tabs')
    def test_error_tabs_teacher_wo_parent(self, make_tabs, is_teacher_url):
        is_teacher_url.return_value = True
        unitLesson = Mock()
        unitLesson.parent = False
        current = 'FAQ'
        path = '/ct/teach/courses/1/units/1/'
        result = error_tabs(path, current, unitLesson)
        make_tabs.assert_called_once_with(
            path, current, ('Resolutions:', 'Resources', 'FAQ', 'Edit')
        )
        self.assertEqual(result, make_tabs())

    @patch('ct.views.is_teacher_url')
    @patch('ct.views.make_tabs')
    @patch('ct.views.make_tab')
    @patch('ct.views.get_object_url')
    def test_error_tabs_teacher_w_parent(self, get_object_url, make_tab, make_tabs, is_teacher_url):
        is_teacher_url.return_value = True
        unitLesson = Mock()
        unitLesson.parent = True
        current = 'FAQ'
        path = '/ct/teach/courses/1/units/1/'
        result = error_tabs(path, current, unitLesson)
        make_tabs.assert_called_once_with(
            path, current, ('Resolutions:', 'Resources', 'FAQ', 'Edit')
        )
        make_tab.assert_called_once_with(path, current, 'Question', get_object_url())
        get_object_url.assert_called_with()
        self.assertEqual(result, make_tabs())

    @patch('ct.views.is_teacher_url')
    @patch('ct.views.make_tabs')
    @patch('ct.views.make_tab')
    @patch('ct.views.get_object_url')
    def test_error_tabs_student(self, get_object_url, make_tab, make_tabs, is_teacher_url):
        is_teacher_url.return_value = False
        unitLesson = Mock()
        unitLesson.parent = True
        current = 'FAQ'
        path = '/ct/courses/1/units/1/'
        error_tabs(path, current, unitLesson)
        make_tabs.assert_called_once_with(
            path, current, ('Resolutions:', 'Resources', 'FAQ')
        )

    def test_make_tab_label_eq_current(self):
        path = Mock()
        current = 'FAQ'
        label = 'FAQ'
        url = Mock()
        result = make_tab(path, current, label, url)
        self.assertEqual(result, (label, '#%sTabDiv' % label))

    def test_make_tab_label_neq_current(self):
        path = Mock()
        current = 'FAQ'
        label = 'Question'
        url = Mock()
        result = make_tab(path, current, label, url)
        self.assertEqual(result, (label, url))

    def test_filter_tabs(self):
        tabs = (('Tab1', '/path/for/tab1/'), ('Tab2', '/path/for/tab2/'), ('Tab3', '/path/for/tab3/'))
        filterLabels = 'Tab2'
        result = filter_tabs(tabs, filterLabels)
        self.assertEqual(result, [('Tab2', '/path/for/tab2/')])

    def test_lesson_tabs(self):
        unitLesson = Mock()
        unitLesson.parent = Mock(pk=1)
        unitLesson.kind = UnitLesson.ANSWERS
        current = 'FAQ'
        path = '/ct/courses/1/units/1/'
        result = lesson_tabs(path, current, unitLesson)
        self.assertEqual(result, [('FAQ', '#FAQTabDiv'), ('Question', '/ct/courses/1/units/1/lessons/1/')])

    def test_lesson_tabs_no_parent(self):
        parent = Mock(pk=2)
        unitLesson = Mock()
        unitLesson.parent = False
        all_mock = Mock()
        all_mock.all.return_value = (parent,)
        unitLesson.get_answers.return_value = all_mock
        unitLesson.kind = UnitLesson.ANSWERS
        current = 'FAQ'
        path = '/ct/courses/1/units/1/'
        result = lesson_tabs(path, current, unitLesson)
        self.assertEqual(
            result,
            [('Study', '/ct/courses/1/units/1//'),
             ('Tasks', '/ct/courses/1/units/1//tasks/'),
             ('Concepts', '/ct/courses/1/units/1//concepts/'),
             ('Errors', '/ct/courses/1/units/1//errors/'),
             ('FAQ', '#FAQTabDiv'),
             ('Answer', '/ct/courses/1/units/1/lessons/2/')]
        )

    @patch('ct.views.get_object_url')
    def test_auto_tabs_error(self, get_object_url):
        path = '/ct/teach/courses/1/units/1/errors/1/'
        current = 'FAQ'
        unitLesson = Mock()
        unitLesson.parent = Mock()
        get_object_url.return_value = '/ct/teach/courses/1/units/1/'
        result = auto_tabs(path, current, unitLesson)
        self.assertEqual(
            result,
            [('Resolutions',
             '/ct/teach/courses/1/units/1/errors/1/'),
             ('Resources', '/ct/teach/courses/1/units/1/errors/1/resources/'),
             ('FAQ', '#FAQTabDiv'),
             ('Edit', '/ct/teach/courses/1/units/1/errors/1/edit/'),
             ('Question', '/ct/teach/courses/1/units/1/')]
        )

    @patch('ct.views.make_tabs')
    def test_unit_tabs(self, make_tabs):
        path = current = Mock()
        unit_tabs(path, current)
        make_tabs.assert_called_once_with(path, current, ('Tasks:', 'Concepts', 'Lessons', 'Resources', 'Edit'), tail=2)

    @patch('ct.views.make_tabs')
    def test_unit_tabs_student(self, make_tabs):
        path = current = Mock()
        unit_tabs_student(path, current)
        make_tabs.assert_called_once_with(path, current, ('Study:', 'Tasks', 'Lessons', 'Concepts'), tail=2)

    @patch('ct.views.make_tabs')
    def test_course_tabs(self, make_tabs):
        path = current = Mock()
        course_tabs(path, current)
        make_tabs.assert_called_once_with(path, current, ('Home:', 'Edit'), tail=2, baseToken='courses')

    def test_ul_page_data(self):
        user = User(username='test_username')
        user.save()
        unit = Unit(title='test title', kind='Courselet', addedBy=user)
        unit.save()
        lesson = Lesson(title='test title', addedBy=user, treeID=1, text='test text')
        lesson.save()
        unit_lesson = UnitLesson.create_from_lesson(lesson, unit)
        request = Mock()
        request.user = user
        request.path = '/ct/courses/1/units/1/lessons/1/'
        request.session = {'fsmID': 1, 'statusMessage': 'test'}
        result = ul_page_data(request, unit.id, unit_lesson.id, 'FAQ')
        self.assertEqual(result[0], unit)
        self.assertEqual(result[1], unit_lesson)
        self.assertIsNone(result[2])
        self.assertIsInstance(result[3], PageData)


class PageDataTests(TestCase):
    """
    Tests for PageData object.
    """
    def test_PageData(self):
        request = Mock()
        request.session = {'fsmID': 1, 'statusMessage': 'test'}
        pageData = PageData(request, test1=1, test2=2)
        self.assertIsInstance(pageData, PageData)
        self.assertIsInstance(pageData.fsmStack, FSMStack)
        self.assertEqual(pageData.test1, 1)
        self.assertEqual(pageData.test2, 2)
        self.assertEqual(pageData.statusMessage, 'test')
        self.assertEqual(request.session, {})
        self.assertEqual(pageData.fsmStack.state, None)

    def test_fsm_redirect_no_state(self):
        request = Mock()
        request.session = {'fsmID': 1, 'statusMessage': 'test'}
        pageData = PageData(request, test1=1, test2=2)
        result = pageData.fsm_redirect(request)
        self.assertIsNone(result)

    def test_fsm_redirect_launch(self):
        request = Mock()
        request.session = {'fsmID': 1, 'statusMessage': 'test'}
        request.method = 'POST'
        request.POST = {'fsmtask': 'launch', 'fsmName': 'testFSMName'}
        pageData = PageData(request, test1=1, test2=2)
        pageData.fsmData = Mock()
        fsmArgs = Mock()
        pageData.fsmData = {'testFSMName': fsmArgs}
        pageData.fsm_push = Mock()
        pageData.fsm_redirect(request)
        pageData.fsm_push.assert_called_with(request, 'testFSMName', fsmArgs)


class BaseViewsTests(TestCase):
    """
    Tests for views.
    """
    def test_main_page_get(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        response = self.client.get(reverse('ct:home'))
        self.assertTemplateUsed(response, 'ct/index.html')
        self.assertEqual(response.status_code, 200)
        self.assertIn('liveSessions', response.context)

    def test_main_page_post_not_fsmstate(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        response = self.client.post(reverse('ct:home'), {'liveID': '1'})
        self.assertEqual(response.status_code, 404)

    @patch('ct.views.get_object_or_404')
    @patch('ct.views.PageData.fsm_push', return_value=HttpResponse(status=200))
    def test_main_page_post_fsmstate(self, fsm_push, get_obj_or_404):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        response = self.client.post(reverse('ct:home'), {'liveID': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_obj_or_404.call_count, 1)
        self.assertEqual(fsm_push.call_count, 1)

    @patch('ct.views.LogoutForm')
    def test_person_profile_same_person(self, LogoutForm):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        response = self.client.get(reverse('ct:person_profile', kwargs={'user_id': self.user.id}))
        self.assertAlmostEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/person.html')
        self.assertIn('You username is', response.content)
        self.assertIn('User profile page', response.content)
        self.assertEqual(LogoutForm.call_count, 1)

    @patch('ct.views.LogoutForm')
    def test_person_profile_post_diff_person(self, LogoutForm):
        self.user = User.objects.create_user(username='test', password='test')
        self.user2 = User.objects.create_user(username='test2', password='test2')
        self.client.login(username='test2', password='test2')
        response = self.client.get(reverse('ct:person_profile', kwargs={'user_id': self.user.id}))
        self.assertAlmostEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/person.html')
        self.assertNotIn('You username is', response.content)
        self.assertIn('User profile page', response.content)
        self.assertEqual(LogoutForm.call_count, 0)

    @patch('ct.views.LogoutForm')
    @patch('ct.views.logout')
    def test_person_profile_post(self, logout, LogoutForm):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        response = self.client.post(
            reverse('ct:person_profile', kwargs={'user_id': self.user.id}),
            {'task': 'logout'}
        )
        self.assertEqual(logout.call_count, 1)
        self.assertRedirects(response, reverse('ct:home'), status_code=302)

    def test_about(self):
        response = self.client.get(reverse('ct:about'))
        self.assertTemplateUsed(response, 'ct/about.html')
        self.assertIn('About Courselets.org', response.content)


class CourseViewTest(TestCase):
    def test_course_view_no_role(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.client.login(username='test', password='test')
        with self.assertRaises(KeyError):
            self.client.get(reverse('ct:course', kwargs={'course_id': self.course.id}))

    def test_course_view_teacher_get_redirect(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        role = Role(course=self.course, user=self.user, role=Role.ENROLLED)
        role.save()
        self.client.login(username='test', password='test')
        response = self.client.get(reverse('ct:course', kwargs={'course_id': self.course.id}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/course.html')
        self.assertRedirects(response, reverse('ct:course_student', kwargs={'course_id': self.course.id}))
        self.assertIn(self.course.title, response.content)

    def test_course_view_teacher_get(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        role.save()
        self.client.login(username='test', password='test')
        response = self.client.get(reverse('ct:course', kwargs={'course_id': self.course.id}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/course.html')
        self.assertIn(self.course.title, response.content)

    def test_course_view_post_new_courselet(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        role.save()
        self.client.login(username='test', password='test')
        response = self.client.post(
            reverse('ct:course', kwargs={'course_id': self.course.id}),
            {'title': 'test_unit_title'},
            follow=True)
        self.assertTemplateUsed(response, 'ct/unit_tasks.html')
        self.assertIn('test_unit_title', response.content)

    @patch('ct.views.Course.reorder_course_unit')
    def test_course_view_post_reorder(self, reorder_course_unit):
        self.user = User.objects.create_user(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit1 = Unit(title='unit1', addedBy=self.user)
        self.unit1.save()
        self.unit2 = Unit(title='unit1', addedBy=self.user)
        self.unit2.save()
        self.course_unit1 = CourseUnit(course=self.course, unit=self.unit1, order=0, addedBy=self.user)
        self.course_unit1.save()
        self.course_unit2 = CourseUnit(course=self.course, unit=self.unit2, order=1, addedBy=self.user)
        self.course_unit2.save()
        role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        role.save()
        self.client.login(username='test', password='test')
        response = self.client.post(
            reverse('ct:course', kwargs={'course_id': self.course.id}),
            {'newOrder': '0', 'oldOrder': '1'},
            follow=True)
        self.assertTemplateUsed(response, 'ct/course.html')
        self.assertEqual(reorder_course_unit.call_count, 1)


class EditCourseTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.client.login(username='test', password='test')

    def test_edit_course_no_role(self):
        self.role.delete()
        with self.assertRaises(KeyError):
            self.client.get(reverse('ct:edit_course', kwargs={'course_id': self.course.id}))

    def test_edit_course_no_course(self):
        response = self.client.get(reverse('ct:edit_course', kwargs={'course_id': 99}))
        self.assertEqual(response.status_code, 404)

    def test_edit_course_student(self):
        self.role.role = Role.ENROLLED
        self.role.save()
        response = self.client.get(reverse('ct:edit_course', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('ct:course_student', args=(self.course.id,)))

    def test_edit_course_get(self):
        response = self.client.get(reverse('ct:edit_course', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/edit_course.html')
        self.assertEqual(response.context['course'], self.course)
        self.assertIsInstance(response.context['courseform'], CourseTitleForm)
        self.assertIn('domain', response.context)

    def test_edit_course_post(self):
        response = self.client.post(
            reverse('ct:edit_course', kwargs={'course_id': self.course.id}),
            {'title': 'test_title', 'access': 'enroll', 'description': 'test_description'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/course.html')
        self.assertIn('test_description', response.content)
        self.assertIn('test_title', response.content)
        course = Course.objects.get(id=self.course.id)
        self.assertEqual(course.access, 'enroll')


class SubscribeTest(TestCase):
    @patch('ct.views.time')
    def test_course_subscribe_tmp_user(self, time):
        time.mktime.return_value = '11011972'
        self.user = User.objects.create_user(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        response = self.client.get(reverse('ct:subscribe', kwargs={'course_id': self.course.id}))
        self.tmp_user = User.objects.filter(username='anonymous'+time.mktime()).first()
        self.assertIsNotNone(self.tmp_user)
        self.assertEqual(self.tmp_user.first_name, 'Temporary User')
        self.assertTrue(Role.objects.filter(course=self.course, user=self.tmp_user, role=Role.SELFSTUDY).exists())
        self.assertTrue(self.tmp_user.groups.filter(name='Temporary').exists())
        self.assertRedirects(response, '/tmp-email-ask/')

    def test_course_subscribe(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        response = self.client.get(reverse('ct:subscribe', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('ct:course_student', args=(self.course.id,)))


class EditUnitTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()

    def test_edit_unit(self):
        response = self.client.get(
            reverse('ct:edit_unit', kwargs={'course_id': self.course.id, 'unit_id': self.unit.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/edit_unit.html')
        self.assertIn('unit', response.context)
        self.assertIn('courseUnit', response.context)
        self.assertIn('unitform', response.context)
        self.assertIn('domain', response.context)
        self.assertEqual(response.context['unit'], self.unit)
        self.assertEqual(response.context['courseUnit'], self.course_unit)
        self.assertIsInstance(response.context['unitform'], UnitTitleForm)

    def test_edit_unit_not_instructor(self):
        self.role.role = Role.ENROLLED
        self.role.save()
        response = self.client.get(
            reverse('ct:edit_unit', kwargs={'course_id': self.course.id, 'unit_id': self.unit.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('ct:study_unit', args=(self.course.id, self.unit.id)))

    def test_edit_unit_post(self):
        response = self.client.post(
            reverse('ct:edit_unit', kwargs={'course_id': self.course.id, 'unit_id': self.unit.id}),
            {'title': 'new test title'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(
            response,
            reverse('ct:unit_tasks', kwargs={'course_id': self.course.id, 'unit_id': self.unit.id})
        )
        self.assertIn('new test title', response.content)
        self.assertIn('unit', response.context)
        self.assertIn('courseUnit', response.context)
        self.assertEqual(response.context['unit'], self.unit)
        self.assertEqual(response.context['courseUnit'], self.course_unit)

    def test_edit_unit_task_release(self):
        response = self.client.post(
            reverse('ct:edit_unit', kwargs={'course_id': self.course.id, 'unit_id': self.unit.id}),
            {'task': 'release'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/edit_unit.html')
        course_unit = CourseUnit.objects.filter(unit=self.unit).first()
        self.assertIsNotNone(course_unit.releaseTime)
        self.assertIn('unit', response.context)
        self.assertIn('courseUnit', response.context)
        self.assertIn('unitform', response.context)
        self.assertIn('domain', response.context)
        self.assertEqual(response.context['unit'], self.unit)
        self.assertEqual(response.context['courseUnit'], self.course_unit)
        self.assertIsInstance(response.context['unitform'], UnitTitleForm)


class UpdateConceptTest(TestCase):
    def test_update_concept_link(self):
        pass


class ConceptsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.lesson = Lesson(title='ugh', text='brr', addedBy=self.user)
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id)
        self.unit_lesson.save()

    def test_unit_concepts(self):
        response = self.client.get(
            reverse('ct:unit_concepts', kwargs={'course_id': self.course.id, 'unit_id': self.unit.id}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/concepts.html')
        self.assertIn('actionTarget', response.context)

    # def test_unit_concepts_post(self):
    #     response = self.client.post(
    #         reverse('ct:unit_concepts', kwargs={'course_id': self.course.id, 'unit_id': self.unit.id}),
    #         {'relationship': 'defines', 'clID': self.lesson.conceptlink_set.filter(concept=self.concept).first().id},
    #         follow=True
    #     )
    #     self.assertEqual(response.status_code, 200)

    def test_copy_unit_lesson_false(self):
        result = copy_unit_lesson(self.unit_lesson, self.concept, self.unit, self.user, None)
        self.assertEqual(result, 'Lesson already in this unit, so no change made.')

    def test_copy_unit_lesson_positive(self):
        unit = Unit(title='test unit title', addedBy=self.user)
        unit.save()
        result = copy_unit_lesson(self.unit_lesson, self.concept, unit, self.user, None)
        self.assertNotEqual(result, self.unit_lesson)

    def test_copy_error_ul_false(self):
        result = copy_error_ul(self.unit_lesson, self.concept, self.unit, self.user, None)
        self.assertEqual(result, 'Lesson already in this unit, so no change made.')

    def test_copy_error_ul_positive(self):
        unit = Unit(title='test unit title', addedBy=self.user)
        unit.save()
        result = copy_error_ul(self.unit_lesson, self.concept, unit, self.user, None)
        self.assertNotEqual(result, self.unit_lesson)

    # def test_live_questions(self):
    #     response = self.client.get(
    #         reverse(
    #             'ct:live_question',
    #             kwargs={'course_id': self.course.id, 'unit_id': self.unit.id, 'ul_id': self.unit_lesson.id}),
    #         follow=True
    #     )
    #     self.assertEqual(response.status_code, 200)


class MakeClTable(TestCase):
    def test_make_cl_table(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        result = make_cl_table(self.concept, self.unit)
        self.assertIsInstance(result, ConceptLinkTable)


class EditLessonTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.lesson = Lesson(title='ugh', text='brr', addedBy=self.user)
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id)
        self.unit_lesson.save()

    def test_edit_lesson(self):
        response = self.client.get(
            reverse(
                'ct:edit_lesson',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id, 'ul_id': self.unit_lesson.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/edit_lesson.html')
        self.assertIn('unitLesson', response.context)
        self.assertIn('atime', response.context)
        self.assertIn('titleform', response.context)
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)
        self.assertIsInstance(response.context['titleform'], LessonForm)

    def test_edit_lesson_update(self):
        response = self.client.post(
            reverse(
                'ct:edit_lesson',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id, 'ul_id': self.unit_lesson.id}
            ),
            {'title': 'new lesson title',
             'kind': 'base',
             'text': 'new test text',
             'medium': 'reading',
             'url': '/test/url/',
             'changeLog': 'test changelog'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/lesson.html')
        self.assertIn('new lesson title', response.content)
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)
        self.assertEqual(response.context['unit'], self.unit)
        self.assertIn('statusTable', response.context)
        self.assertIn('evalTable', response.context)
        self.assertIn('answer', response.context)
        self.assertIn('addForm', response.context)
        self.assertIn('roleForm', response.context)

    def test_edit_lesson_delete(self):
        response = self.client.post(
            reverse(
                'ct:edit_lesson',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id, 'ul_id': self.unit_lesson.id}
            ),
            {'task': 'delete'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(UnitLesson.objects.filter(id=self.unit_lesson.id).exists())
        self.assertTemplateUsed(response, 'ct/lessons.html')
        for context_var in ('lessonSet', 'searchForm', 'msg',
                            'lessonForm', 'conceptLinks',
                            'actionLabel', 'lessonTable',
                            'creationInstructions',
                            'showReorderForm',
                            'foundNothing'):
            self.assertIn(context_var, response.context)


class ResolutionsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.lesson = Lesson(title='ugh', text='brr', addedBy=self.user, concept=self.concept)
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(
            unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id, kind=UnitLesson.MISUNDERSTANDS
        )
        self.unit_lesson.save()

    def test_resolutions(self):
        response = self.client.get(
            reverse(
                'ct:resolutions',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id, 'ul_id': self.unit_lesson.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/lessons.html')

    def test_resolutions_create_lesson(self):
        response = self.client.post(
            reverse(
                'ct:resolutions',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id, 'ul_id': self.unit_lesson.id}
            ),
            {'title': 'new lesson title',
             'kind': 'errmod',
             'text': 'new test text',
             'medium': 'reading',
             'url': '/test/url/',
             'changeLog': 'test changelog'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UnitLesson.objects.filter(lesson__title='new lesson title', kind=UnitLesson.RESOLVES).exists())
        self.assertTemplateUsed(response, 'ct/lessons.html')
        self.assertIn('new lesson title', response.content)

    def test_link_resolution_ul(self):
        parentUL = Mock()
        ul = em = addedBy = unit = Mock()
        link_resolution_ul(ul, em, unit, addedBy, parentUL)
        parentUL.copy_resolution.assert_called_once_with(ul, addedBy)


class ErrorResourcesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.concept_graph_to_from = ConceptGraph(toConcept=self.concept, fromConcept=self.concept, addedBy=self.user)
        self.concept_graph_to_from.save()
        self.lesson = Lesson(title='ugh', text='brr', addedBy=self.user, concept=self.concept)
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(
            unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id, kind=UnitLesson.MISUNDERSTANDS
        )
        self.unit_lesson.save()

    def test_error_resources(self):
        response = self.client.get(
            reverse(
                'ct:error_resources',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id, 'ul_id': self.unit_lesson.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/error_resources.html')
        for context_var in ('toConcepts', 'fromConcepts', 'testLessons', 'alternativeDefs'):
            self.assertIn(context_var, response.context)
        self.assertEqual(response.context['toConcepts'][0], self.concept_graph_to_from)
        self.assertEqual(response.context['fromConcepts'][0], self.concept_graph_to_from)


class SlideShowTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()

    def test_slideshow(self):
        response = self.client.get(
            reverse(
                'ct:slideshow',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/study_unit.html')
        self.assertIn('unit', response.context)
        self.assertIn('startForm', response.context)
        self.assertEqual(response.context['unit'], self.unit)
        self.assertIsInstance(response.context['startForm'], TaskForm)

    @patch('ct.views.PageData')
    def test_slideshow_post_start(self, PageData):
        pageData = Mock()
        pageData.fsm_push.return_value = HttpResponse('It is ok', status=200)
        PageData.return_value = pageData
        response = self.client.post(
            reverse(
                'ct:slideshow',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id}
            ),
            {'task': 'start'},
            follow=True
        )
        self.assertEqual(pageData.fsm_push.call_count, 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'It is ok')


class UnitLessonTaskStudentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()

    def test_unit_tasks_student(self):
        response = self.client.get(
            reverse(
                'ct:unit_tasks_student',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/unit_tasks_student.html')
        self.assertIn('test unit title', response.content)

    def test_unit_tasks_student_no_unit(self):
        unit_id = self.unit.id
        self.unit.delete()
        response = self.client.get(
            reverse(
                'ct:unit_tasks_student',
                kwargs={'course_id': self.course.id, 'unit_id': unit_id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 404)


class UnitLessonsStudentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()

    def test_unit_lessons_student_404(self):
        unit_id = self.unit.id
        self.unit.delete()
        response = self.client.get(
            reverse(
                'ct:unit_lessons_student',
                kwargs={'course_id': self.course.id, 'unit_id': unit_id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_unit_lessons_student(self):
        response = self.client.get(
            reverse(
                'ct:unit_lessons_student',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/lessons_student.html')
        self.assertIn('test unit title', response.content)


class ConceptLinkTableTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.concept_link_table = ConceptLinkTable(data=(self.concept,))

    def test_concept_link_table_append(self):
        self.assertEqual(self.concept_link_table.data[0][0], self.concept)
        self.assertIsInstance(self.concept_link_table.data[0][1], ConceptLinkForm)

    def test_concept_link_table_replace(self):
        new_concept_form = ConceptLinkForm(instance=self.concept)
        self.concept_link_table.replace(self.concept, new_concept_form)
        self.assertEqual(self.concept_link_table.data[0][0], self.concept)
        self.assertEqual(self.concept_link_table.data[0][1], new_concept_form)

    def test_concept_link_table_remove(self):
        result = self.concept_link_table.remove(self.concept)
        self.assertTrue(result)
        self.assertEqual(self.concept_link_table.data, [])

    def test_concept_link_table_move_between_tables(self):
        new_table = ConceptLinkTable()
        self.concept_link_table.move_between_tables(self.concept, new_table)
        self.assertEqual(new_table.data[0][0], self.concept)
        self.assertIsInstance(new_table.data[0][1], ConceptLinkForm)
        self.concept_link_table.move_between_tables(self.concept, new_table)
        self.assertEqual(self.concept_link_table.data[0][0], self.concept)
        self.assertIsInstance(self.concept_link_table.data[0][1], ConceptLinkForm)


class UnitConceptsStudentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()

    def test_unit_concepts_student_404(self):
        unit_id = self.unit.id
        self.unit.delete()
        response = self.client.get(
            reverse(
                'ct:unit_concepts_student',
                kwargs={'course_id': self.course.id, 'unit_id': unit_id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_unit_concepts_student(self):
        response = self.client.get(
            reverse(
                'ct:unit_concepts_student',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/concepts_student.html')
        self.assertIn('test unit title', response.content)


class LessonNextUrlTest(TestCase):
    def setUp(self):
        self.request = Mock()
        self.course_id = Mock()
        self.nextUL = Mock()
        self.ul = Mock()
        self.ul.get_next_lesson.return_value = self.nextUL

    def test_lesson_next_url(self):
        lesson_next_url(self.request, self.ul, self.course_id)
        self.nextUL.get_study_url.assert_called_once_with(self.course_id)

    @patch('ct.views.get_base_url')
    def test_lesson_next_url_exception(self, get_base_url):
        self.ul.get_next_lesson.return_value = None
        self.ul.get_next_lesson.side_effect = UnitLesson.DoesNotExist
        lesson_next_url(self.request, self.ul, self.course_id)
        get_base_url.assert_called_once_with(self.request.path, ['tasks'])


class LessonTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.lesson = Lesson(title='ugh', text='brr', addedBy=self.user)
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id)
        self.unit_lesson.save()

    def test_lesson_get(self):
        response = self.client.get(
            reverse(
                'ct:lesson',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id, 'ul_id': self.unit_lesson.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/lesson_student.html')
        self.assertIn('unitLesson', response.context)
        self.assertIn('unit', response.context)
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)
        self.assertEqual(response.context['unit'], self.unit)

    def test_lesson_post(self):
        response = self.client.post(
            reverse(
                'ct:lesson',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id, 'ul_id': self.unit_lesson.id}
            ),
            {'liked': 'on'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/unit_tasks_student.html')
        self.assertRedirects(response, reverse('ct:unit_tasks_student', args=(self.course.id, self.unit.id)))
        self.assertTrue(Liked.objects.filter(unitLesson=self.unit_lesson, addedBy=self.user).exists())


class UlTasksStudentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.lesson = Lesson(title='ugh', text='brr', addedBy=self.user, kind=Lesson.ORCT_QUESTION)
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id)
        self.unit_lesson.save()
        self.unit_lesson.response_set.create(lesson=self.lesson, course=self.course, text='test text', author=self.user)

    def test_ul_tasks_student(self):
        response = self.client.get(
            reverse(
                'ct:ul_tasks_student',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id, 'ul_id': self.unit_lesson.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/lesson_tasks.html')
        self.assertEqual(
            response.context['responseTable'],
            [(self.unit_lesson.response_set.first(), 'assess', 'self-assess your answer')]
        )
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)
        self.assertEqual(response.context['unit'], self.unit)


class UlTasksTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.lesson = Lesson(
            title='ugh', text='brr', addedBy=self.user, kind=Lesson.ORCT_QUESTION, concept=self.concept
        )
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id)
        self.unit_lesson.save()
        self.response = Response(
            unitLesson=self.unit_lesson,
            lesson=self.lesson,
            course=self.course,
            text='test text',
            author=self.user,
            kind=Response.STUDENT_QUESTION
        )
        self.response.save()
        self.student_error = StudentError(response=self.response, errorModel=self.unit_lesson, author=self.user)
        self.student_error.save()

    def test_ul_tasks(self):
        unit_lesson_error = UnitLesson(
            unit=self.unit,
            lesson=self.lesson,
            addedBy=self.user,
            treeID=self.lesson.id,
            kind=UnitLesson.MISUNDERSTANDS,
            parent=self.unit_lesson
        )
        unit_lesson_error.save()
        unit_lesson_answer = UnitLesson(
            unit=self.unit,
            lesson=self.lesson,
            addedBy=self.user,
            treeID=self.lesson.id,
            kind=UnitLesson.ANSWERS,
            parent=self.unit_lesson
        )
        unit_lesson_answer.save()
        response = self.client.get(
            reverse(
                'ct:ul_tasks',
                kwargs={
                  'course_id': self.course.id,
                  'unit_id': self.unit.id,
                  'ul_id': self.unit_lesson.id,
                }
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/ul_tasks.html')
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)
        self.assertEqual(response.context['unit'], self.unit)
        self.assertEqual(response.context['errorTable'], [(unit_lesson_error, 0)])
        self.assertIn('newInquiries', response.context)

    def test_ul_tasks_kind_not_question(self):
        self.lesson.kind = Lesson.PRACTICE_EXAM
        self.lesson.save()
        response = self.client.get(
            reverse(
                'ct:ul_tasks',
                kwargs={
                  'course_id': self.course.id,
                  'unit_id': self.unit.id,
                  'ul_id': self.unit_lesson.id,
                }
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/ul_tasks.html')
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)
        self.assertEqual(response.context['unit'], self.unit)
        self.assertEqual(response.context['errorTable'], ())
        self.assertIn('errorTable', response.context)
        self.assertIn('newInquiries', response.context)


class StudyConceptTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.lesson = Lesson(title='ugh', text='brr', addedBy=self.user, kind=Lesson.ORCT_QUESTION)
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id)
        self.unit_lesson.save()
        self.unit_lesson.response_set.create(lesson=self.lesson, course=self.course, text='test text', author=self.user)

    def test_study_concept(self):
        response = self.client.get(
            reverse(
                'ct:study_concept',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id, 'ul_id': self.unit_lesson.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/concept_student.html')
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)


class ConceptLessonsStudentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.lesson = Lesson(
            title='ugh', text='brr', addedBy=self.user, kind=Lesson.ORCT_QUESTION, concept=self.concept
        )
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id)
        self.unit_lesson.save()
        self.unit_lesson.response_set.create(lesson=self.lesson, course=self.course, text='test text', author=self.user)

    def test_concept_lessons_student(self):
        response = self.client.get(
            reverse(
                'ct:concept_lessons_student',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id, 'ul_id': self.unit_lesson.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/concept_lessons_student.html')
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)
        self.assertEqual(response.context['unit'], self.unit)
        self.assertEqual(response.context['clTable'], [self.concept.conceptlink_set.first()])


class ResolutionsStudentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.lesson = Lesson(
            title='ugh', text='brr', addedBy=self.user, kind=Lesson.ORCT_QUESTION, concept=self.concept
        )
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id)
        self.unit_lesson.save()
        self.response = Response(
            unitLesson=self.unit_lesson, lesson=self.lesson, course=self.course, text='test text', author=self.user
        )
        self.response.save()
        self.student_error = StudentError(response=self.response, errorModel=self.unit_lesson, author=self.user)
        self.student_error.save()

    def test_resolutions_student(self):
        response = self.client.get(
            reverse(
                'ct:resolutions_student',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id, 'ul_id': self.unit_lesson.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/resolutions_student.html')
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)
        self.assertEqual(response.context['unit'], self.unit)
        self.assertIn('lessonTable', response.context)
        self.assertIn('statusForm', response.context)

    def test_resolutions_student_error_form_post(self):
        response = self.client.post(
            reverse(
                'ct:resolutions_student',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id, 'ul_id': self.unit_lesson.id}
            ),
            {'status': 'help'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/resolutions_student.html')
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)
        self.assertEqual(response.context['unit'], self.unit)
        self.assertIn('lessonTable', response.context)
        self.assertIn('statusForm', response.context)


class ul_faq_studentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.lesson = Lesson(
            title='ugh', text='brr', addedBy=self.user, kind=Lesson.ORCT_QUESTION, concept=self.concept
        )
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id)
        self.unit_lesson.save()
        self.response = Response(
            unitLesson=self.unit_lesson,
            lesson=self.lesson,
            course=self.course,
            text='test text',
            author=self.user,
            kind=Response.STUDENT_QUESTION
        )
        self.response.save()
        self.student_error = StudentError(response=self.response, errorModel=self.unit_lesson, author=self.user)
        self.student_error.save()

    def test_ul_faq_student(self):
        response = self.client.get(
            reverse(
                'ct:ul_faq_student',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id, 'ul_id': self.unit_lesson.id}
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/faq_student.html')
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)
        self.assertEqual(response.context['unit'], self.unit)
        self.assertEqual(response.context['faqTable'], [(self.response, 0)])
        self.assertIn('faqTable', response.context)
        self.assertIn('form', response.context)

    def test_ul_faq_student_comment_form_post(self):
        response = self.client.post(
            reverse(
                'ct:ul_faq_student',
                kwargs={'course_id': self.course.id, 'unit_id': self.unit.id, 'ul_id': self.unit_lesson.id}
            ),
            {'title': 'test comment title', 'text': 'test text', 'confidence': Response.GUESS},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/faq_student.html')
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)
        self.assertEqual(response.context['unit'], self.unit)
        self.assertIn('faqTable', response.context)
        self.assertEqual(len(response.context['faqTable']), 2)
        self.assertIn('form', response.context)


class UlThreadStudentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.lesson = Lesson(
            title='ugh', text='brr', addedBy=self.user, kind=Lesson.ORCT_QUESTION, concept=self.concept
        )
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id)
        self.unit_lesson.save()
        self.response = Response(
            unitLesson=self.unit_lesson,
            lesson=self.lesson,
            course=self.course,
            text='test text',
            author=self.user,
            kind=Response.STUDENT_QUESTION
        )
        self.response.save()
        self.student_error = StudentError(response=self.response, errorModel=self.unit_lesson, author=self.user)
        self.student_error.save()

    def test_ul_thread_student(self):
        response = self.client.get(
            reverse(
                'ct:ul_thread_student',
                kwargs={
                  'course_id': self.course.id,
                  'unit_id': self.unit.id,
                  'ul_id': self.unit_lesson.id,
                  'resp_id': self.response.id
                }
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/thread_student.html')
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)
        self.assertEqual(response.context['unit'], self.unit)
        self.assertIn('faqTable', response.context)
        self.assertIn('form', response.context)
        self.assertIn('inquiry', response.context)
        self.assertIn('errorTable', response.context)
        self.assertIn('replyTable', response.context)

    def test_ul_thread_student_reply_form_post(self):
        response = self.client.post(
            reverse(
                'ct:ul_thread_student',
                kwargs={
                  'course_id': self.course.id,
                  'unit_id': self.unit.id,
                  'ul_id': self.unit_lesson.id,
                  'resp_id': self.response.id
                }
            ),
            {'title': 'test comment title', 'text': 'test text', 'confidence': Response.GUESS, 'task': 'meToo'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/thread_student.html')
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)
        self.assertEqual(response.context['unit'], self.unit)
        self.assertIn('faqTable', response.context)
        self.assertIn('form', response.context)
        self.assertIn('inquiry', response.context)
        self.assertIn('errorTable', response.context)
        self.assertIn('replyTable', response.context)


class UlRespondTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.lesson = Lesson(
            title='ugh', text='brr', addedBy=self.user, kind=Lesson.ORCT_QUESTION, concept=self.concept
        )
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id)
        self.unit_lesson.save()
        self.response = Response(
            unitLesson=self.unit_lesson,
            lesson=self.lesson,
            course=self.course,
            text='test text',
            author=self.user,
            kind=Response.STUDENT_QUESTION
        )
        self.response.save()
        self.student_error = StudentError(response=self.response, errorModel=self.unit_lesson, author=self.user)
        self.student_error.save()

    def test_ul_respond(self):
        response = self.client.get(
            reverse(
                'ct:ul_respond',
                kwargs={
                  'course_id': self.course.id,
                  'unit_id': self.unit.id,
                  'ul_id': self.unit_lesson.id,
                }
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/ask.html')
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)
        self.assertIn('form', response.context)
        self.assertIn('qtext', response.context)

    def test_ul_respond_response_form_post(self):
        response = self.client.post(
            reverse(
                'ct:ul_respond',
                kwargs={
                  'course_id': self.course.id,
                  'unit_id': self.unit.id,
                  'ul_id': self.unit_lesson.id,
                }
            ),
            {'title': 'test comment title', 'text': 'test text', 'confidence': Response.GUESS},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/assess.html')


class AssessTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.lesson = Lesson(
            title='ugh', text='brr', addedBy=self.user, kind=Lesson.ORCT_QUESTION, concept=self.concept
        )
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id)
        self.unit_lesson.save()
        self.response = Response(
            unitLesson=self.unit_lesson,
            lesson=self.lesson,
            course=self.course,
            text='test text',
            author=self.user,
            kind=Response.STUDENT_QUESTION
        )
        self.response.save()
        self.student_error = StudentError(response=self.response, errorModel=self.unit_lesson, author=self.user)
        self.student_error.save()

    def test_assess_self_empty_access_form(self):
        response = self.client.get(
            reverse(
                'ct:assess',
                kwargs={
                  'course_id': self.course.id,
                  'unit_id': self.unit.id,
                  'ul_id': self.unit_lesson.id,
                  'resp_id': self.response.id
                }
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/assess.html')
        self.assertIn('response', response.context)
        self.assertIn('answer', response.context)
        self.assertIn('assessForm', response.context)
        self.assertIn('showAnswer', response.context)

    def test_assess_self_access_form_and_liked_form_post(self):
        response = self.client.post(
            reverse(
                'ct:assess',
                kwargs={
                  'course_id': self.course.id,
                  'unit_id': self.unit.id,
                  'ul_id': self.unit_lesson.id,
                  'resp_id': self.response.id
                }
            ),
            {'selfeval': 'correct', 'status': 'review', 'liked': 'on'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/unit_tasks_student.html')
        self.assertEqual(response.context['unit'], self.unit)
        self.assertIn('taskTable', response.context)
        self.assertTrue(Liked.objects.filter(unitLesson=self.response.unitLesson, addedBy=self.user).exists())

    def test_assess_student_error(self):
        response = self.client.post(
            reverse(
                'ct:assess',
                kwargs={
                  'course_id': self.course.id,
                  'unit_id': self.unit.id,
                  'ul_id': self.unit_lesson.id,
                  'resp_id': self.response.id
                }
            ),
            {'selfeval': 'different', 'status': 'review', 'liked': 'on'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/assess.html')
        self.assertIn('response', response.context)
        self.assertIn('answer', response.context)
        self.assertNotIn('assessForm', response.context)
        self.assertIn('showAnswer', response.context)
        self.assertTrue(Liked.objects.filter(unitLesson=self.response.unitLesson, addedBy=self.user).exists())


class AssessErrorsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(course=self.course, unit=self.unit, order=0, addedBy=self.user)
        self.course_unit.save()
        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()
        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)
        self.lesson = Lesson(
            title='ugh', text='brr', addedBy=self.user, kind=Lesson.ORCT_QUESTION, concept=self.concept
        )
        self.lesson.save_root(self.concept)
        self.unit_lesson = UnitLesson(unit=self.unit, lesson=self.lesson, addedBy=self.user, treeID=self.lesson.id)
        self.unit_lesson.save()
        self.response = Response(
            unitLesson=self.unit_lesson,
            lesson=self.lesson,
            course=self.course,
            text='test text',
            author=self.user,
            kind=Response.STUDENT_QUESTION
        )
        self.response.save()
        self.student_error = StudentError(response=self.response, errorModel=self.unit_lesson, author=self.user)
        self.student_error.save()

    def test_assess_errors(self):
        response = self.client.get(
            reverse(
                'ct:assess_errors',
                kwargs={
                  'course_id': self.course.id,
                  'unit_id': self.unit.id,
                  'ul_id': self.unit_lesson.id,
                  'resp_id': self.response.id
                }
            ),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/assess.html')
        self.assertIn('response', response.context)
        self.assertIn('answer', response.context)
        self.assertIn('errorModels', response.context)
        self.assertIn('showAnswer', response.context)

    def test_assess_errors_post(self):
        response = self.client.post(
            reverse(
                'ct:assess_errors',
                kwargs={
                  'course_id': self.course.id,
                  'unit_id': self.unit.id,
                  'ul_id': self.unit_lesson.id,
                  'resp_id': self.response.id
                }
            ),
            {'emlist': self.unit_lesson.id},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/lesson_tasks.html')
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)
        self.assertEqual(response.context['unit'], self.unit)
        self.assertIn('unitLesson', response.context)
        self.assertIn('unit', response.context)
        self.assertIn('responseTable', response.context)
        self.assertIn('errorTable', response.context)
        self.assertFalse(StudentError.objects.filter(status='review').exists())

    def test_assess_errors_post_new_user(self):
        self.user_new = User.objects.create_user(username='test2', password='test2')
        self.client.login(username='test2', password='test2')
        response = self.client.post(
            reverse(
                'ct:assess_errors',
                kwargs={
                  'course_id': self.course.id,
                  'unit_id': self.unit.id,
                  'ul_id': self.unit_lesson.id,
                  'resp_id': self.response.id
                }
            ),
            {'emlist': self.unit_lesson.id},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ct/lesson_tasks.html')
        self.assertEqual(response.context['unitLesson'], self.unit_lesson)
        self.assertEqual(response.context['unit'], self.unit)
        self.assertIn('unitLesson', response.context)
        self.assertIn('unit', response.context)
        self.assertIn('responseTable', response.context)
        self.assertIn('errorTable', response.context)
        self.assertTrue(StudentError.objects.filter(status='review').exists())
