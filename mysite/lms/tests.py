import datetime
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import patch, Mock
from chat.models import Chat, EnrollUnitCode, Message
from ct.models import Course, Unit, CourseUnit, Role, Concept, Lesson, UnitLesson
from views import CourseView
from django.utils import timezone
import json

class TestCourseView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')

    @patch('lms.views.ChatProgressSerializer')
    @patch('lms.views.get_object_or_404')
    @patch('lms.views.EnrollUnitCode.get_code')
    @patch('fsm.models.FSMState.find_live_sessions')
    @patch('chat.models.Chat.objects.filter')
    def test_course_view(self, chatFilterMock, find_live_sessions, get_code, get_obj_or_404, ChatProgressSerializer):
        """
        This test tests that:
         - query FSMState.find_live_sessions(request.user).filter(activity__course=course).first()
           return live session and this live session is present in page's context
        """
        filter_mock = Mock()
        filter_mock.filter = Mock()

        find_live_sessions.return_value = filter_mock

        first_mock = Mock()
        filter_mock.filter.return_value = first_mock
        first_mock.first = Mock()
        first_mock.first.return_value = Mock()
        first_mock.first.return_value.id = 1

        unit = Mock()
        unit.unit.get_exercises.return_value=[Mock()]
        course_mock = Mock()
        course_units = Mock()
        course_mock.get_course_units = course_units
        course_units.return_value = [unit]
        get_obj_or_404.return_value = course_mock

        chatFilterMock = Mock()
        chatFilterMock.return_value = [Mock()]

        ChatProgressSerializer.data.get.return_value = 0

        response = self.client.get(reverse('lms:course_view', kwargs={'course_id': 1}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(filter_mock.filter.call_count, 1)
        self.assertEqual(first_mock.first.call_count, 1)
        self.assertEqual(get_obj_or_404.call_count, 1)

        self.assertTemplateUsed(response, 'lms/course_page.html')
        # context should contain these keys: course, liveSession, courslets
        self.assertIn('course', response.context)
        self.assertIn('liveSession', response.context)
        self.assertIn('courslets', response.context)

    def test_course_view_negative(self):
        """
        This test tests case when teacher not yet (opened) joined live session and
        student opens course page.
        Student should not see 'Join Live Session' button on the top of the page.
        """
        self.course = Course(
            title='Great Course', description='the bestest', addedBy=self.user
        )
        self.course.save()

        response = self.client.get(
            reverse('lms:course_view', kwargs={'course_id': self.course.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lms/course_page.html')
        self.assertIn('course', response.context)
        self.assertIn('liveSession', response.context)
        self.assertIn('courslets', response.context)
        self.assertEqual(response.context['liveSession'], None)
        self.assertFalse(response.context['liveSession'])

    #TODO: write test when teacher really creates Course and Courslets inside of the course and student open page.
    #TODO: user should see 'Join' button.


class TestCourseletViewHistoryTab(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.login(username='test', password='test')

        self.course = Course(title='test_title', addedBy=self.user)
        self.course.save()
        self.unit = Unit(title='test unit title', addedBy=self.user)
        self.unit.save()
        self.course_unit = CourseUnit(
            course=self.course,
            unit=self.unit,
            order=0,
            addedBy=self.user
        )
        self.course_unit.releaseTime = timezone.now() - datetime.timedelta(days=1)
        self.course_unit.save()

        self.enroll = EnrollUnitCode(courseUnit=self.course_unit)
        self.enroll.save()

        self.role = Role(course=self.course, user=self.user, role=Role.INSTRUCTOR)
        self.role.save()

        self.student_role = Role(course=self.course, user=self.user, role=Role.ENROLLED)
        self.student_role.save()

        self.concept = Concept.new_concept('bad', 'idea', self.unit, self.user)

        self.lesson = Lesson(
            title='New York Test Lesson',
            text='brr',
            addedBy=self.user,
            kind=Lesson.ORCT_QUESTION
        )
        self.lesson.save_root(self.concept)

        self.unit_lesson = UnitLesson(
            unit=self.unit,
            lesson=self.lesson,
            addedBy=self.user,
            treeID=self.lesson.id,
            order=0
        )
        self.unit_lesson.save()

        self.unit_lesson_answer = UnitLesson(
            parent=self.unit_lesson,
            unit=self.unit,
            lesson=self.lesson,
            addedBy=self.user,
            treeID=self.lesson.id,
            kind=UnitLesson.ANSWERS
        )
        self.unit_lesson_answer.save()

        self.user = User.objects.create_user(username='admin', password='admin')

        call_command('fsm_deploy')

    def test_courslet_history_tab(self):
        '''
        tests that if we have a chat with state == None this chat will be shown in history tab.
        :return:
        '''
        # test that there's no history yet
        response = self.client.get(
            reverse('lms:course_view', kwargs={'course_id': self.course.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['courslet_history']), 0)
        self.assertTrue(len(response.context['courslets']) > 0)

        # now we call chat:chat_enroll view to init chat
        response = self.client.get(
            reverse('chat:chat_enroll', kwargs={'enroll_key': self.enroll.enrollCode})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Chat.objects.all().count(), 1)

        chat = Chat.objects.all().first()
        self.assertIsNotNone(chat)
        chat.state = None
        chat.save()

        response = self.client.get(
            reverse('lms:course_view', kwargs={'course_id': self.course.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['courslet_history']), 1)
        self.assertTrue(len(list(response.context['courslets'])) > 0)

    def test_click_on_courslet_creates_new_chat(self):
        # test that there's no history yet
        response = self.client.get(
            reverse('lms:course_view', kwargs={'course_id': self.course.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['courslet_history']), 0)
        self.assertIsNotNone(list(response.context['courslets']))

        self.assertEqual(response.status_code, 200)

        chats_count_1 = Chat.objects.all().count()

        response = self.client.get(
            reverse('chat:chat_enroll', kwargs={'enroll_key': self.enroll.enrollCode})
        )
        self.assertEqual(response.context['chat'].id, Chat.objects.all().first().id)
        self.assertEqual(response.status_code, 200)
        chats_count_2 = Chat.objects.count()

        self.assertNotEqual(chats_count_2, chats_count_1)

        response = self.client.get(
            reverse('chat:chat_enroll', kwargs={'enroll_key': self.enroll.enrollCode})
        )
        chats_count_3 = Chat.objects.count()

        response = self.client.get(
            reverse('chat:chat_enroll', kwargs={'enroll_key': self.enroll.enrollCode})
        )
        chats_count_4 = Chat.objects.count()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(chats_count_4, chats_count_2)
        self.assertEqual(chats_count_3, chats_count_2)

        self.assertEqual(response.context['chat'].id, Chat.objects.all().first().id)

        chat = Chat.objects.all().first()
        # get chat and set state to None it means that courslet finished.
        chat.state = None
        chat.save()

        response = self.client.get(
            reverse('lms:course_view', kwargs={'course_id': self.course.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Chat.objects.count(), chats_count_2)
        self.assertEqual(len(list(response.context['courslets'])), 1)
        self.assertEqual(len(response.context['courslet_history']), 1)

    def test_courslet_history(self):
        enroll_code = EnrollUnitCode.get_code(self.course_unit)
        chat_id = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code,)), follow=True
        ).context['chat_id']

        response = self.client.get(
            reverse('chat:history'), {'chat_id': chat_id}, follow=True
        )
        json_content = json.loads(response.content)

        next_url = json_content['input']['url']

        answer = 'My Answer'
        response = self.client.put(
            next_url,
            data=json.dumps({"text": answer, "chat_id": chat_id}),
            content_type='application/json',
            follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        response = self.client.get(
            next_url, {'chat_id': chat_id}, follow=True
        )

        json_content = json.loads(response.content)
        next_url = json_content['input']['url']

        self.assertIsNotNone(json_content['input']['options'])
        self.assertEquals(len(json_content['addMessages']), 2)

        # emulate chat finished - set state to None

        Chat.objects.filter(id=chat_id).update(state=None)

        response = self.client.get(
            reverse('chat:chat_enroll', args=(enroll_code, chat_id)), follow=True
        )
        response = self.client.get(
            reverse('chat:history'), {'chat_id': chat_id}, follow=True
        )
        json_content = json.loads(response.content)

        self.assertIsNone(json_content['input']['options'])
        self.assertEquals(len(json_content['addMessages']), 4)














