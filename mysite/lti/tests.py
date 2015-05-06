# coding=utf-8

import json
import oauth2
from mock import patch
from django.test import TestCase, Client
from django.contrib.auth.models import User

from lti.models import LTIUser
from ct.models import Course, Role
from psa.models import UserSocialAuth


class LTITestCase(TestCase):
    def setUp(self):
        """Preconditions."""
        self.client = Client()

        self.user = User(username='test_user',
                         email='test@test.com')
        self.user.save()

        mocked_nonce = u'135685044251684026041377608307'
        mocked_timestamp = u'1234567890'
        mocked_decoded_signature = u'my_signature='
        self.headers = {
            u'user_id': 1,
            u'lis_person_name_full': u'Test Username',
            u'lis_person_name_given': u'First',
            u'lis_person_name_family': u'Second',
            u'lis_person_contact_email_primary': u'test@test.com',
            u'oauth_callback': u'about:blank',
            u'launch_presentation_return_url': '',
            u'lti_message_type': u'basic-lti-launch-request',
            u'lti_version': 'LTI-1p0',
            u'roles': u'Student',
            u'context_id': 1,
            u'ext_lms': u'moodle-2',

            u'resource_link_id': 'dfgsfhrybvrth',
            u'lis_result_sourcedid': 'wesgaegagrreg',

            u'oauth_nonce': mocked_nonce,
            u'oauth_timestamp': mocked_timestamp,
            u'oauth_consumer_key': u'',
            u'oauth_signature_method': u'HMAC-SHA1',
            u'oauth_version': u'1.0',
            u'oauth_signature': mocked_decoded_signature
        }

        self.course = Course(title='test title',
                             description='test description',
                             access='Public',
                             addedBy=self.user)
        self.course.save()


class MethodsTest(LTITestCase):
    """Test for correct request method passed in view."""

    def test_post(self):
        with patch('lti.views.DjangoToolProvider') as mocked:
            mocked.return_value.is_valid_request.return_value = True
            response = self.client.post('/lti/ct/courses/1/',
                                        data=self.headers,
                                        follow=True)
            self.assertTemplateUsed(response, template_name='ct/course.html')

    def test_failure_post(self):
        with patch('lti.views.DjangoToolProvider') as mocked:
            mocked.return_value.is_valid_request.return_value = False
            response = self.client.post('/lti/ct/courses/1/',
                                        data=self.headers,
                                        follow=True)
            self.assertTemplateUsed(response, template_name='lti/error.html')

    def test_get(self):
        with patch('lti.views.DjangoToolProvider') as mocked:
            mocked.return_value.is_valid_request.return_value = True
            response = self.client.get('/lti/ct/courses/1/',
                                       follow=True)
            self.assertTemplateUsed(response, template_name='lti/error.html')


class ParamsTest(LTITestCase):
    """Test different params handling."""

    def test_ext_lms(self):
        del self.headers[u'ext_lms']
        with patch('lti.views.DjangoToolProvider') as mocked:
            mocked.return_value.is_valid_request.return_value = True
            self.client.post('/lti/ct/courses/1/',
                             data=self.headers,
                             follow=True)
            self.assertTrue(LTIUser.objects.filter(consumer='lti').exists())

    def test_roles_prof(self):
        self.headers.update({u'roles': u'Instructor'})
        with patch('lti.views.DjangoToolProvider') as mocked:
            mocked.return_value.is_valid_request.return_value = True
            self.client.post('/lti/ct/courses/1/',
                             data=self.headers,
                             follow=True)
            self.assertTrue(Role.objects.filter(role='prof').exists())

    def test_roles_student(self):
        self.headers.update({u'roles': u'Leaner'})
        with patch('lti.views.DjangoToolProvider') as mocked:
            mocked.return_value.is_valid_request.return_value = True
            self.client.post('/lti/ct/courses/1/',
                             data=self.headers,
                             follow=True)
            self.assertTrue(Role.objects.filter(role='student').exists())

    def test_user_id(self):
        del self.headers[u'user_id']
        with patch('lti.views.DjangoToolProvider') as mocked:
            mocked.return_value.is_valid_request.return_value = True
            response = self.client.post('/lti/ct/courses/1/',
                                        data=self.headers,
                                        follow=True)
            self.assertTemplateUsed(response, template_name='lti/error.html')

    def test_roles_none(self):
        del self.headers[u'roles']
        with patch('lti.views.DjangoToolProvider') as mocked:
            mocked.return_value.is_valid_request.return_value = True
            self.client.post('/lti/ct/courses/1/',
                             data=self.headers,
                             follow=True)
            self.assertTrue(Role.objects.filter(role='student').exists())

    def test_lti_user(self):
        """Default LTI user creation process"""
        with patch('lti.views.DjangoToolProvider') as mocked:
            mocked.return_value.is_valid_request.return_value = True
            self.client.post('/lti/ct/courses/1/',
                             data=self.headers,
                             follow=True)
            self.assertTrue(LTIUser.objects.filter(consumer='moodle-2').exists())
            self.assertTrue(Role.objects.filter(role='student').exists())
            self.assertEqual(LTIUser.objects.get(consumer='moodle-2').django_user,
                             UserSocialAuth.objects.get(
                                 uid=self.headers[u'lis_person_contact_email_primary']
                             ).user)
            self.assertEqual(self.user, UserSocialAuth.objects.get(
                uid=self.headers[u'lis_person_contact_email_primary']
            ).user)

    def test_lti_user_no_email(self):
        del self.headers[u'lis_person_contact_email_primary']
        with patch('lti.views.DjangoToolProvider') as mocked:
            mocked.return_value.is_valid_request.return_value = True
            self.client.post('/lti/ct/courses/1/',
                             data=self.headers,
                             follow=True)
            self.assertTrue(LTIUser.objects.filter(consumer='moodle-2').exists())
            self.assertTrue(Role.objects.filter(role='student').exists())
            self.assertNotEqual(LTIUser.objects.get(consumer='moodle-2').django_user,
                                User.objects.get(id=1))

    def test_lti_user_no_username_no_email(self):
        """Test for non-existent username field

        If there is no username in POST
        we create user with username==user_id
        """
        del self.headers[u'lis_person_name_full']
        del self.headers[u'lis_person_contact_email_primary']
        with patch('lti.views.DjangoToolProvider') as mocked:
            mocked.return_value.is_valid_request.return_value = True
            self.client.post('/lti/ct/courses/1/',
                             data=self.headers,
                             follow=True)
            self.assertTrue(LTIUser.objects.filter(consumer='moodle-2').exists())
            self.assertTrue(Role.objects.filter(role='student').exists())
            self.assertNotEqual(LTIUser.objects.get(consumer='moodle-2').django_user,
                                User.objects.get(id=1))
            self.assertEqual(LTIUser.objects.get(consumer='moodle-2').
                             django_user.username,
                             LTIUser.objects.get(consumer='moodle-2').user_id)

    def test_lti_user_link_social(self):
        """Default LTI user creation process"""
        social = UserSocialAuth(
            user=self.user,
            uid=self.headers[u'lis_person_contact_email_primary'],
            provider='email'
        )
        social.save()
        with patch('lti.views.DjangoToolProvider') as mocked:
            mocked.return_value.is_valid_request.return_value = True
            self.client.post('/lti/ct/courses/1/',
                             data=self.headers,
                             follow=True)
            self.assertTrue(LTIUser.objects.filter(consumer='moodle-2').exists())
            self.assertTrue(Role.objects.filter(role='student').exists())
            self.assertEqual(LTIUser.objects.get(consumer='moodle-2').django_user,
                             social.user)


class ExceptionTest(LTITestCase):
    """Test raising exception."""

    def test_missing_signature(self):
        with patch('lti.views.DjangoToolProvider') as mocked:
            mocked.return_value.is_valid_request.side_effect = oauth2.MissingSignature()
            response = self.client.get('/lti/ct/courses/1/', follow=True)
            self.assertTemplateUsed(response, template_name='lti/error.html')

    def test_oauth_error(self):
        with patch('lti.views.DjangoToolProvider') as mocked:
            mocked.return_value.is_valid_request.side_effect = oauth2.Error()
            response = self.client.get('/lti/ct/courses/1/', follow=True)
            self.assertTemplateUsed(response, template_name='lti/error.html')

    def test_key_error(self):
        with patch('lti.views.DjangoToolProvider') as mocked:
            mocked.return_value.is_valid_request.side_effect = KeyError()
            response = self.client.get('/lti/ct/courses/1/', follow=True)
            self.assertTemplateUsed(response, template_name='lti/error.html')

    def test_attribute_error(self):
        with patch('lti.views.DjangoToolProvider') as mocked:
            mocked.return_value.is_valid_request.side_effect = AttributeError()
            response = self.client.get('/lti/ct/courses/1/', follow=True)
            self.assertTemplateUsed(response, template_name='lti/error.html')


class ModelTest(LTITestCase):
    """Test model LTIUser."""

    def test_lti_user(self):
        lti_user = LTIUser(user_id=1,
                           consumer='test_consimer',
                           extra_data=json.dumps(self.headers),
                           django_user=self.user,
                           course_id=1)
        lti_user.save()

        self.assertTrue(lti_user.is_linked)
        self.assertFalse(lti_user.is_enrolled('student', 1))

        lti_user.enroll('student', 1)
        self.assertTrue(lti_user.is_enrolled('student', 1))

    def test_lti_user_create_links(self):
        lti_user = LTIUser(user_id=1,
                           consumer='test_consimer',
                           extra_data=json.dumps(self.headers),
                           course_id=1)
        lti_user.save()

        self.assertFalse(lti_user.is_linked)
        lti_user.create_links()
        self.assertTrue(lti_user.is_linked)
