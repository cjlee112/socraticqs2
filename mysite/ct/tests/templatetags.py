"""
Unit tests for ct/templatetags.
"""
import inspect

from datetime import timedelta
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User
from django.template import Context, Template

from mock import patch
from ddt import ddt, data, unpack

from ct.models import UnitLesson, Course, Unit, Concept, Lesson, ConceptLink, Response
from ct.templatetags.ct_extras import *


@override_settings(SUSPEND_SIGNALS=True)
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

    @patch('ct.templatetags.ct_extras.pypandoc')
    def test_md2html_pandoc_exception(self, pypandoc):
        pypandoc.convert.side_effect = StandardError
        rendered = self.render_template(
            '{% load ct_extras %}'
            '{{ test_text | md2html }}',
            context=self.context
        )
        self.assertEqual(rendered, self.context['test_text'])

    @data('get_base_url', 'get_path_type')
    def test_get_base_url_exception(self, helper):
        with self.assertRaises(ValueError):
            getattr(inspect.getmodule(self), helper).__call__(
                '/ct/courses/1/units/1/lessons/1/', baseToken='non_existent_token'
            )

    def test_get_object_url_exception(self):
        self.context['ul'] = self.unit  # Unit object does not have get_url method
        rendered = self.render_template(
            '{% load ct_extras %}'
            '{{ actionTarget | get_object_url:ul }}',
            context=self.context
        )
        self.assertEqual(rendered, '/ct/courses/1/units/1/unit/1/teach/')

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

    def test_find_audio(self):
        result = find_audio('test tag head .. audio:: test tag tail \n', 4)
        self.assertEqual(result, (14, 39, 'test tag tail'))

    def test_audio_html(self):
        """
        Function should return string for embeding audio into html.
        """
        result = audio_html('audio.mp3')
        self.assertEqual(
            result,
            '''<audio controls><source src="audio.ogg" type="audio/ogg"><source src="audio.mp3" '''
            '''type="audio/mpeg">no support for audio!</audio>'''
        )

    def test_video_html(self):
        """
        Function should return string for embeding youtube or vimeo link.
        """
        result = video_html('youtube:test_video_path')
        self.assertIn('test_video_path', result)
        self.assertIn('src="https://www.youtube.com/embed/', result)

        result = video_html('vimeo:test_video_path')
        self.assertIn('test_video_path', result)
        self.assertIn('src="https://player.vimeo.com/video/', result)

    def test_video_html_with_exception(self):
        """
        Test exception handling.
        """
        result = video_html('youtube')
        self.assertEqual(result, 'ERROR: bad video source: youtube')

        result = video_html('some_new_cdn:test_video_path')
        self.assertEqual(result, 'ERROR: unknown video sourceDB: some_new_cdn')

    def test_add_replace_temporary_markers(self):
        """
        Test add_temporary_markers and replace_temporary_markers in tandem.
        """
        result = add_temporary_markers('test tag head .. audio:: test tag tail \n', find_audio)
        self.assertEqual(result, ('test tag head mArKeR:0:\n', [('mArKeR:0:', 'test tag tail')]))

        result = replace_temporary_markers(result[0], audio_html, result[1])
        self.assertEqual(
            result,
            '''test tag head <audio controls><source src="test tag tail.ogg" type="audio/ogg">'''
            '''<source src="test tag tail.mp3" type="audio/mpeg">no support for audio!</audio>\n'''
        )
