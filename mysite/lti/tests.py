# coding=utf-8

import json
import oauth2

from mock import patch, Mock
from ddt import ddt, data, unpack
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from psa.models import UserSocialAuth
from ct.models import Course, Role, Unit, CourseUnit
from lti.models import LTIUser, CourseRef
from lti.views import create_courseref


class LTITestCase(TestCase):
    def setUp(self):
        """
        Preconditions.
        """
        self.client = Client()
        self.user = User.objects.create_user('test', 'test@test.com', 'test')

        mocked_nonce = u'135685044251684026041377608307'
        mocked_timestamp = u'1234567890'
        mocked_decoded_signature = u'my_signature='
        self.headers = {
            u'user_id': 1,
            u'lis_person_name_full': u'Test Username',
            u'lis_person_name_given': u'First',
            u'lis_person_name_family': u'Second',
            u'lis_person_contact_email_primary': u'test@test.com',
            u'lis_person_sourcedid': u'Test_Username',
            u'oauth_callback': u'about:blank',
            u'launch_presentation_return_url': '',
            u'lti_message_type': u'basic-lti-launch-request',
            u'lti_version': 'LTI-1p0',
            u'roles': u'Student',
            u'context_id': 1,
            u'tool_consumer_info_product_family_code': u'moodle',
            u'context_title': u'Test title',
            u'tool_consumer_instance_guid': u'test.dot.com',

            u'resource_link_id': 'dfgsfhrybvrth',
            u'lis_result_sourcedid': 'wesgaegagrreg',

            u'oauth_nonce': mocked_nonce,
            u'oauth_timestamp': mocked_timestamp,
            u'oauth_consumer_key': u'',
            u'oauth_signature_method': u'HMAC-SHA1',
            u'oauth_version': u'1.0',
            u'oauth_signature': mocked_decoded_signature
        }

        self.unit = Unit(title='Test title', addedBy=self.user)
        self.unit.save()
        self.course = Course(title='Test title',
                             description='test description',
                             access='Public',
                             enrollCode='111',
                             lockout='222',
                             addedBy=self.user)
        self.course.save()
        self.course_ref = CourseRef(
            course=self.course, context_id=self.headers.get('context_id'),
            tc_guid=self.headers.get('tool_consumer_instance_guid')
        )
        self.course_ref.save()
        self.course_ref.instructors.add(self.user)

        self.courseunit = CourseUnit(
            unit=self.unit, course=self.course,
            order=0, addedBy=self.user
        )
        self.courseunit.save()


@patch('lti.views.DjangoToolProvider')
class MethodsTest(LTITestCase):
    """
    Test for correct request method passed in view.
    """
    def test_post(self, mocked):
        mocked.return_value.is_valid_request.return_value = True
        response = self.client.post('/lti/',
                                    data=self.headers,
                                    follow=True)
        self.assertTemplateUsed(response, template_name='ct/course.html')

    def test_failure_post(self, mocked):
        mocked.return_value.is_valid_request.return_value = False
        response = self.client.post('/lti/',
                                    data=self.headers,
                                    follow=True)
        self.assertTemplateUsed(response, template_name='lti/error.html')

    def test_get(self, mocked):
        mocked.return_value.is_valid_request.return_value = True
        response = self.client.get('/lti/',
                                   follow=True)
        self.assertTemplateUsed(response, template_name='lti/error.html')


@ddt
@patch('lti.views.DjangoToolProvider')
class ParamsTest(LTITestCase):
    """
    Test different params handling.
    """

    def test_tool_consumer_info_product_family_code(self, mocked):
        del self.headers[u'tool_consumer_info_product_family_code']
        mocked.return_value.is_valid_request.return_value = True
        self.client.post('/lti/',
                         data=self.headers,
                         follow=True)
        self.assertTrue(LTIUser.objects.filter(consumer='lti').exists())

    @unpack
    @data((Role.INSTRUCTOR, {u'roles': u'Instructor'}),
          (Role.ENROLLED, {u'roles': u'Learner'}))
    def test_roles(self, role, header, mocked):
        self.headers.update(header)
        mocked.return_value.is_valid_request.return_value = True
        self.client.post('/lti/',
                         data=self.headers,
                         follow=True)
        self.assertTrue(Role.objects.filter(role=role).exists())

    def test_user_id(self, mocked):
        del self.headers[u'user_id']
        mocked.return_value.is_valid_request.return_value = True
        response = self.client.post('/lti/',
                                    data=self.headers,
                                    follow=True)
        self.assertTemplateUsed(response, template_name='lti/error.html')

    def test_roles_none(self, mocked):
        del self.headers[u'roles']
        mocked.return_value.is_valid_request.return_value = True
        self.client.post('/lti/',
                         data=self.headers,
                         follow=True)
        self.assertTrue(Role.objects.filter(role=Role.ENROLLED).exists())

    def test_lti_user(self, mocked):
        """
        Default LTI user creation process.
        """
        mocked.return_value.is_valid_request.return_value = True
        self.client.post('/lti/',
                         data=self.headers,
                         follow=True)
        self.assertTrue(LTIUser.objects.filter(consumer='moodle').exists())
        self.assertTrue(Role.objects.filter(role=Role.ENROLLED).exists())
        self.assertEqual(LTIUser.objects.get(consumer='moodle').django_user,
                         UserSocialAuth.objects.get(
                             uid=self.headers[u'lis_person_contact_email_primary']
                         ).user)
        self.assertEqual(self.user, UserSocialAuth.objects.get(
            uid=self.headers[u'lis_person_contact_email_primary']
        ).user)

    def test_lti_user_no_email(self, mocked):
        del self.headers[u'lis_person_contact_email_primary']
        mocked.return_value.is_valid_request.return_value = True
        self.client.post('/lti/',
                         data=self.headers,
                         follow=True)
        self.assertTrue(LTIUser.objects.filter(consumer='moodle').exists())
        self.assertTrue(Role.objects.filter(role=Role.ENROLLED).exists())
        self.assertNotEqual(LTIUser.objects.get(consumer='moodle').django_user,
                            User.objects.get(id=self.user.id))

    def test_lti_user_no_username_no_email(self, mocked):
        """Test for non-existent username field

        If there is no username in POST
        we create user with username==user_id
        """
        del self.headers[u'lis_person_name_full']
        del self.headers[u'lis_person_contact_email_primary']
        mocked.return_value.is_valid_request.return_value = True
        self.client.post('/lti/',
                         data=self.headers,
                         follow=True)
        self.assertTrue(LTIUser.objects.filter(consumer='moodle').exists())
        self.assertTrue(Role.objects.filter(role=Role.ENROLLED).exists())
        self.assertNotEqual(LTIUser.objects.get(consumer='moodle').django_user,
                            User.objects.get(id=self.user.id))
        self.assertEqual(LTIUser.objects.get(consumer='moodle').
                         django_user.username,
                         self.headers.get('lis_person_sourcedid'))

    def test_lti_user_link_social(self, mocked):
        """
        Default LTI user creation process.
        """
        social = UserSocialAuth(
            user=self.user,
            uid=self.headers[u'lis_person_contact_email_primary'],
            provider='email'
        )
        social.save()
        mocked.return_value.is_valid_request.return_value = True
        self.client.post('/lti/',
                         data=self.headers,
                         follow=True)
        self.assertTrue(LTIUser.objects.filter(consumer='moodle').exists())
        self.assertTrue(Role.objects.filter(role=Role.ENROLLED).exists())
        self.assertEqual(LTIUser.objects.get(consumer='moodle').django_user,
                         social.user)


@ddt
@patch('lti.views.DjangoToolProvider')
class ExceptionTest(LTITestCase):
    """
    Test raising exception.
    """
    @data(oauth2.MissingSignature, oauth2.Error, KeyError, AttributeError)
    def test_exceptions(self, exception, mocked):
        mocked.return_value.is_valid_request.side_effect = exception()
        response = self.client.get('/lti/', follow=True)
        self.assertTemplateUsed(response, template_name='lti/error.html')


class ModelTest(LTITestCase):
    """
    Test model LTIUser.
    """
    def test_lti_user(self):
        """Test enrollment process"""
        lti_user = LTIUser(user_id=self.user.id,
                           consumer='test_consumer',
                           extra_data=json.dumps(self.headers),
                           django_user=self.user,
                           context_id=1)
        lti_user.save()

        self.assertFalse(lti_user.is_enrolled('student', self.course.id))

        lti_user.enroll('student', self.course.id)
        self.assertTrue(lti_user.is_enrolled('student', self.course.id))

    def test_lti_user_create_links(self):
        """Creating LTIUser without Django user

        Testing Django user creation process.
        """
        lti_user = LTIUser(user_id=self.user.id,
                           consumer='test_consumer',
                           extra_data=json.dumps(self.headers),
                           context_id=1)
        lti_user.save()

        self.assertFalse(lti_user.is_linked)
        lti_user.create_links()
        self.assertTrue(lti_user.is_linked)


@ddt
@patch('lti.views.DjangoToolProvider')
class TestCourseRef(LTITestCase):
    """
    Testing CourseRef object.
    """
    def test_course_ref_roles(self, mocked):
        """Test different action for different roles"""
        mocked.return_value.is_valid_request.return_value = True
        self.course_ref.delete()
        response = self.client.post('/lti/', data=self.headers, follow=True)
        self.assertFalse(CourseRef.objects.filter(course=self.course).exists())
        self.assertTemplateUsed(response, 'lti/error.html')

    def test_create_courseref_only_lti(self, mocked):
        """
        Test that only LTI is allowed.
        """
        request = Mock()
        request.session = {}
        res = create_courseref(request)
        self.assertEqual(res.content, 'Only LTI allowed')

    @unpack
    @data(('1', 'ct:course'), ('1111', 'ct:edit_course'))
    def test_create_courseref_existence(self, context_id, langing_page, mocked):
        """
        Test for existence/non-existence of CourseRef.
        """
        _id = self.course.id if context_id == '1' else self.course.id + 1
        lti_post = {'context_id': context_id,
                    'context_title': 'test title',
                    'tool_consumer_instance_guid': 'test.dot.com',
                    'roles': 'Instructor'}
        request = Mock()
        request.user = self.user
        request.session = {'LTI_POST': lti_post,
                           'is_valid': True}
        res = create_courseref(request)
        self.assertEqual(res.url, reverse(langing_page, args=(_id,)))


@patch('lti.views.DjangoToolProvider')
class TestUnit(LTITestCase):
    """
    Testing Unit template rendering.
    """
    def test_unit_render(self, mocked):
        mocked.return_value.is_valid_request.return_value = True
        response = self.client.post(
            '/lti/unit/{}/'.format(self.unit.id), data=self.headers, follow=True
        )
        self.assertTemplateUsed(response, 'ct/study_unit.html')
