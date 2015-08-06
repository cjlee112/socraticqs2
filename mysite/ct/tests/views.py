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


class ViewsTests(TestCase):
    """
    Tests for views.
    """
    def test_main_page_get(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')
        response = self.client.get(reverse('ct:home'))
        self.assertTemplateUsed(response, 'ct/index.html')
        self.assertEqual(response.status_code, 200)

