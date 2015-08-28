"""
Unit tests for ct/templatetags.
"""
from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.template import Context, Template

from mock import patch
from ddt import ddt, data, unpack

from ct.models import UnitLesson, Course, Unit, Concept, Lesson, ConceptLink, Response
from ct.templatetags.ct_extras import *


@ddt
class TagsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.concept = Concept(title='test title', addedBy=self.user)
        self.concept.save()
        self.lesson = Lesson(title='ugh', text='brr', addedBy=self.user, kind=Lesson.ORCT_QUESTION)
        self.lesson.save_root()
        self.lesson.add_concept_link(self.concept, ConceptLink.TESTS, self.user)
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.unit_lesson = UnitLesson(unit=self.unit, addedBy=self.user, treeID=42, lesson=self.lesson)
        self.unit_lesson.save()
        self.response = Response(
            course=self.course,
            lesson=self.lesson,
            author=self.user,
            unitLesson=self.unit_lesson,
            confidence=Response.GUESS,
            title='test title',
            text='test text'
        )
        self.response.save()
        self.context = {
            'actionTarget': '/ct/courses/1/units/1/',
            'ul': self.unit_lesson,
            'test_text': 'This is a test text',
            'r': self.response
        }

    def render_template(self, string, context=None):
        context = context or {}
        context = Context(context)
        return Template(string).render(context)

    @unpack
    @data(
        ('{{ test_text | md2html }}', '<p>This is a test text</p>\n'),
        ('{{ actionTarget | get_object_url:ul }}', '/ct/courses/1/units/1/lessons/1/'),
        ('{{ actionTarget | get_home_url:ul }}', '/ct/courses/1/units/1/lessons/1/'),
        ('{{ actionTarget | get_thread_url:r }}', '/ct/courses/1/units/1/lessons/1/faq/1/'),
        ('{{ actionTarget | get_tasks_url:ul }}', '/ct/courses/1/units/1/lessons/1/tasks/'),
        ('{{ actionTarget | get_dummy_navbar }}', '<li><a href="/ct/courses/1/">Course</a></li>'),
    )
    def test_all_filters(self, template_variable, expected_result):
        rendered = self.render_template(
            '{% load ct_extras %}' + template_variable,
            context=self.context
        )
        self.assertEqual(rendered, expected_result)

    @patch('ct.templatetags.ct_extras.timezone')
    def test_display_datetime(self, timezone_patched):
        saved_time = timezone.now()
        timezone_patched.now.return_value = saved_time
        context = {'dt': saved_time - timedelta(1)}
        rendered = self.render_template(
            '{% load ct_extras %}'
            '{{ dt|display_datetime }}',
            context=context
        )
        self.assertEqual(rendered, '1 day ago')
