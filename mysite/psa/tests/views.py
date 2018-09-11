import mock
import unittest
from uuid import uuid4
from django.core.urlresolvers import reverse
from django.core import mail
from django.db import IntegrityError
from django.http import HttpResponse
from django.test import TestCase, Client
from django.test.client import RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.conf import settings
from importlib import import_module

from social_core.exceptions import (AuthAlreadyAssociated,
                               AuthException,
                               InvalidEmail, AuthMissingParameter)
from accounts.models import Instructor
from ctms.models import Invite
from psa.custom_django_storage import CustomCode

from psa.views import (context,
                       validation_sent,
                       custom_login,
                       done)
from psa.pipeline import (social_user,
                          not_allowed_to_merge,
                          associate_user,
                          associate_by_email,
                          social_merge,
                          union_merge,
                          validated_user_details,
                          custom_mail_validation)
from psa.mail import send_validation
from psa.custom_backends import EmailAuth


class ViewsUnitTest(TestCase):
    """
    Functional tests.
    """
    def setUp(self):
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()  # we need to make load() work, or the cookie is worthless

        self.factory = RequestFactory()
        self.request = self.factory.get('/login/')
        self.client = Client()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key
        self.client.get('/login/')

        self.request.session = self.client.session
        self.request.session['email_validation_address'] = 'test@test.com'

    def test_context(self):
        """
        Need to return avaliable_backends variable.
        """
        result = context()
        self.assertTrue('available_backends' in result)

    def test_validation_sent(self):
        anonymous = AnonymousUser()
        self.request.user = anonymous
        self.request.current_page = None
        response = validation_sent(self.request)
        self.assertIsInstance(response, HttpResponse)
        self.assertTrue('test@test.com' in response.content)

    def test_custom_login_get(self):
        self.request.current_page = None
        anonymous = AnonymousUser()
        self.request.user = anonymous
        response = custom_login(self.request)
        self.assertIsInstance(response, HttpResponse)
        self.assertTrue('LoginForm' in response.content)

    def test_custom_login_post_negative(self):
        self.client = Client()
        credentials = {'username': 'test',
                       'password': 'test'}
        response = self.client.post('/login/', data=credentials)
        self.assertTemplateUsed(
            response,
            template_name='psa/custom_login.html'
        )

    def test_custom_login_post_positive(self):
        user = User(username='test')
        user.set_password('test')
        user.save()
        self.client = Client()
        credentials = {'username': 'test',
                       'password': 'test'}
        response = self.client.post('/login/', data=credentials, follow=True)
        self.assertRedirects(response, expected_url='/ct/')
        self.assertTemplateUsed(response, template_name='ct/index.html')

    def test_login_by_email(self):
        user = User(username='test', email='test@test.cc')
        user.set_password('test')
        user.save()
        self.client = Client()
        credentials = {'email': 'test@test.cc'}
        response = self.client.post(reverse('complete') + '?next=/ct/', data=credentials, follow=True)
        self.assertRedirects(response, reverse('ctms:email_sent'))
        self.assertTemplateUsed(response, 'ctms/email_sent.html')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Confirm your email on Courselets')

    @unittest.skip("skip unless fixed")
    def test_new_login_with_u_hash_in_session(self):
        """
        If user send request with u_hash in post equals to u_hash in session
        user will be redirected to ctms:shared_courses page
        """
        user = User(username='test', email='test@aa.cc')
        user.set_password('test')
        user.save()
        Instructor.objects.create(user=user, institution='sdfsdf')
        u_hash = uuid4().hex
        self.client.session['u_hash'] = u_hash
        self.client.session.save()

        credentials = {
            'email': 'test@aa.cc',
            'password': 'test',
            'u_hash': u_hash
        }
        response = self.client.post(reverse('new_login'), data=credentials, follow=True)
        self.assertRedirects(response, reverse('ctms:shared_courses'))

    @unittest.skip("skip unless fixed")
    def test_new_login_without_u_hash_in_session(self):
        """
        If user send request with u_hash in post equals to u_hash in session
        user will be redirected to ctms:shared_courses page
        """
        user = User(username='test', email='test@aa.cc')
        user.set_password('test')
        user.save()
        Instructor.objects.create(user=user, institution='sdfsdf')
        self.client = Client()

        credentials = {
            'email': 'test@aa.cc',
            'password': 'test',
        }
        response = self.client.post(reverse('new_login'), data=credentials, follow=True)
        self.assertRedirects(response, '/ct/')

    def test_done(self):
        user = User(username='test_user')
        user.set_password('test')
        user.save()
        self.request.user = user
        self.request.current_page = None
        response = done(self.request)
        self.assertIsInstance(response, HttpResponse)
        self.assertTrue('test_user' in response.content)

    def test_ask_stranger(self):
        user = User(username='test')
        user.set_password('test')
        user.save()
        self.client = Client()
        credentials = {'username': 'test',
                       'password': 'test'}
        self.client.post('/login/', data=credentials, follow=True)
        response = self.client.get('/tmp-email-ask/')
        self.assertIsInstance(response, HttpResponse)
        self.assertTrue('email-required-modal' in response.content)

    def test_set_pass_false(self):
        user = User(username='test')
        user.set_password('test')
        user.save()
        self.client = Client()
        credentials = {'username': 'test',
                       'password': 'test'}
        self.client.post('/login/', data=credentials, follow=True)
        response = self.client.get('/set-pass/')
        self.assertTrue('Something goes wrong' in response.content)
        self.assertTemplateUsed(response, template_name='ct/person.html')

    def test_set_pass_true(self):
        user = User(username='test')
        user.set_password('test')
        user.save()
        self.client = Client()
        credentials_for_login = {'username': 'test',
                                 'password': 'test'}
        credentials_for_set_pass = {'pass': 'test2',
                                    'confirm': 'test2'}
        self.client.post('/login/',
                         data=credentials_for_login,
                         follow=True)
        response = self.client.post(
            '/set-pass/',
            data=credentials_for_set_pass,
            follow=True
        )
        self.assertTemplateUsed(response, template_name='ct/person.html')
        self.assertTrue('Your password was changed' in response.content)
        user = User.objects.get(username='test')
        self.assertTrue(user.check_password('test2'))


class TestSocialUser(TestCase):
    """
    Test for social_user pipeline.
    """
    def setUp(self):
        self.exists = mock.Mock()
        self.exists.exists.return_value = False

        self.user = mock.Mock()
        self.user.groups.filter.return_value = self.exists
        self.main_user = mock.Mock()
        self.main_user.groups.filter.return_value = self.exists
        self.social = mock.Mock()
        self.social.user = self.user

        self.exists_anonym = mock.Mock()
        self.exists_anonym.exists.return_value = True
        self.anonymous = mock.Mock()
        self.anonymous.groups.filter.return_value = self.exists_anonym
        self.attrs = {'strategy.storage.user.get_social_auth.return_value': self.social}

    def test_no_social(self):
        self.attrs = {'strategy.storage.user.get_social_auth.return_value': []}
        backend = mock.Mock(**self.attrs)
        backend.name = 'google-oauth2'
        uid = 'test@test.com'

        res = social_user(backend, uid)
        self.assertEqual(res['user'], None)
        self.assertEqual(res['social'], [])
        self.assertEqual(res['is_new'], True)
        self.assertEqual(res['new_association'], False)

    def test_social_stranger(self):
        backend = mock.Mock(**self.attrs)
        backend.name = 'google-oauth2'
        uid = 'test@test.com'

        res = social_user(backend, uid)
        self.assertEqual(res['user'], self.user)
        self.assertEqual(res['social'], self.social)
        self.assertEqual(res['is_new'], False)
        self.assertEqual(res['new_association'], False)

    def test_social_validated(self):
        backend = mock.Mock(**self.attrs)
        backend.name = 'google-oauth2'
        uid = 'test@test.com'

        with mock.patch('psa.pipeline.not_allowed_to_merge') as mocked:
            mocked.return_value = False
            res = social_user(backend, uid, user=self.main_user)
        self.assertEqual(res['user'], self.main_user)
        self.assertEqual(res['social'], self.social)
        self.assertEqual(res['is_new'], False)
        self.assertEqual(res['new_association'], False)

    def test_social_validated_not_allowed(self):
        backend = mock.Mock(**self.attrs)
        backend.name = 'google-oauth2'
        uid = 'test@test.com'

        with mock.patch('psa.pipeline.not_allowed_to_merge') as mocked:
            mocked.return_value = True
            with self.assertRaises(AuthAlreadyAssociated):
                social_user(backend, uid, user=self.main_user)

    def test_social_anonymous(self):
        backend = mock.Mock(**self.attrs)
        backend.name = 'google-oauth2'
        uid = 'test@test.com'

        res = social_user(backend, uid, user=self.anonymous)
        self.assertEqual(res['user'], self.user)
        self.assertEqual(res['social'], self.social)
        self.assertEqual(res['is_new'], False)
        self.assertEqual(res['new_association'], False)


class NotAllowedToMergeTest(TestCase):
    """
    Test not_allowed_to_merge function.
    """
    def setUp(self):
        self.user1 = mock.Mock()
        self.user2 = mock.Mock()

        self.provider1 = mock.Mock()
        self.provider2 = mock.Mock()
        self.provider3 = mock.Mock()

        self.provider1.provider = 'facebook'
        self.provider2.provider = 'google'
        self.provider3.provider = 'twitter'

        self.user1.social_auth = mock.Mock()
        self.user2.social_auth = mock.Mock()

    def test_not_allowed_to_merge_false(self):
        self.user1.social_auth.all = mock.Mock(
            return_value=(self.provider1, self.provider2)
        )
        self.user2.social_auth.all = mock.Mock(return_value=(self.provider3,))

        res = bool(not_allowed_to_merge(self.user1, self.user2))
        self.assertFalse(res)

    def test_not_allowed_to_merge_true(self):
        self.user1.social_auth.all = mock.Mock(
            return_value=(self.provider1, self.provider2)
        )
        self.user2.social_auth.all = mock.Mock(
            return_value=(self.provider2, self.provider3)
        )
        res = bool(not_allowed_to_merge(self.user1, self.user2))
        self.assertTrue(res)


class AssociateUserTest(TestCase):
    """
    Test for associate_user pipeline.
    """
    def setUp(self):
        self.details = {'email': 'test@test.com'}
        self.user = mock.Mock()
        self.social = mock.Mock()
        self.social.user = mock.Mock()
        self.backend = mock.Mock()

    def test_associate_user_create_secondary(self):
        self.backend.strategy.storage.user.create_social_auth = mock.Mock(return_value=self.social)

        with mock.patch('psa.pipeline.SecondaryEmail') as mocked:
            save = mock.Mock()
            save.return_value = None
            mocked.return_value = save
            res = associate_user(self.backend, self.details,
                                 'test@test.com', user=self.user)
            self.assertEqual(res['social'], self.social)
            self.assertEqual(res['user'], self.social.user)
            self.assertEqual(res['new_association'], True)

    def test_associate_user_raise_exception(self):
        create_sa = mock.Mock(side_effect=Exception())
        self.backend.strategy.storage.user.create_social_auth = create_sa
        self.backend.strategy.storage.is_integrity_error = mock.Mock(return_value=False)

        with self.assertRaises(Exception):
            associate_user(
                self.backend,
                self.details,
                'test@test.com',
                user=self.user
            )

    def test_associate_user_handle_exception(self):
        create_sa = mock.Mock(side_effect=Exception())
        self.backend.strategy.storage.user.create_social_auth = create_sa
        self.backend.strategy.storage.is_integrity_error = mock.Mock(return_value=True)

        with mock.patch('psa.pipeline.social_user') as mocked:
            mocked.return_value = mock.Mock()
            res = associate_user(
                self.backend,
                self.details,
                'test@test.com',
                user=self.user
            )
            self.assertEqual(res, mocked.return_value)


class AssociateByEmailTest(TestCase):
    """
    Test associate_by_email pipeline.
    """
    def setUp(self):
        self.user = mock.Mock()
        self.backend = mock.Mock()
        self.details = mock.Mock()

    def test_return_none(self):
        self.assertEqual(associate_by_email(self.backend, self.details, user=self.user), None)

    def test_without_email(self):
        self.details.get = mock.Mock(return_value=None)
        self.assertEqual(associate_by_email(self.backend, self.details, user=None), None)

    def test_no_users_founded_by_email_and_no_social(self):
        self.backend.strategy.storage.user.get_users_by_email = mock.Mock(return_value=[])
        self.details.get = mock.Mock(return_value='test@test.com')
        self.assertEqual(associate_by_email(self.backend, self.details, user=None), None)

    def test_no_users_founded_by_email_and_social(self):
        self.backend.strategy.storage.user.get_users_by_email = mock.Mock(return_value=[])
        self.details.get = mock.Mock(return_value='test@test.com')

        with mock.patch('psa.pipeline.UserSocialAuth.objects.filter') as mocked:
            social = mock.Mock()
            social.user = mock.Mock()
            social_qs = mock.Mock()
            social_qs.first = mock.Mock(return_value=social)
            mocked.return_value = social_qs

            res = associate_by_email(self.backend, self.details, user=None)
            self.assertEqual(res['user'], social.user)

    def test_no_users_founded_by_email_and_users_gt_one(self):
        self.backend.strategy.storage.user.get_users_by_email = mock.Mock(return_value=[1, 2])
        self.details.get = mock.Mock(return_value='test@test.com')

        with self.assertRaises(AuthException):
            associate_by_email(self.backend, self.details, user=None)

    def test_no_users_founded_by_email_and_users_eq_one(self):
        self.backend.strategy.storage.user.get_users_by_email = mock.Mock(return_value=[self.user])
        self.details.get = mock.Mock(return_value='test@test.com')

        res = associate_by_email(self.backend, self.details, user=None)
        self.assertEqual(res['user'], self.user)


class SocialMergeTest(TestCase):
    """
    Test social_merge function.
    """
    def test_social_merge(self):
        update = mock.Mock()
        update.update = mock.Mock()
        tmp_user, user = (mock.Mock(), mock.Mock())
        tmp_user.social_auth.all = mock.Mock(return_value=update)
        tmp_user.lti_auth.all = mock.Mock(return_value=update)

        calls = [mock.call(user=user), mock.call(django_user=user)]

        social_merge(tmp_user, user)
        update.update.assert_has_calls(calls, any_order=True)


class UnionMergeTest(TestCase):
    """
    Test union_merge function.
    """
    def test_union_merge(self):
        save = mock.Mock()
        role1, role2, role3 = (mock.Mock(), mock.Mock(), mock.Mock())
        for role in (role1, role2, role3):
            role.role = mock.Mock()
            role.course = mock.Mock()
            role.save = save
        tmp_user, user = (mock.Mock(), mock.Mock())
        tmp_user.role_set.all = mock.Mock(return_value=(role1, role2, role3,))
        user.role_set.filter = mock.Mock(return_value=None)

        unitstatus1, unitstatus2 = (mock.Mock(), mock.Mock())
        for unitstatus in (unitstatus1, unitstatus2):
            unitstatus.save = save
        tmp_user.unitstatus_set.all = mock.Mock(return_value=(unitstatus1,
                                                              unitstatus2))

        update = mock.Mock()
        update.update = mock.Mock()
        tmp_user.fsmstate_set.all = mock.Mock(return_value=update)
        tmp_user.response_set.all = mock.Mock(return_value=update)
        tmp_user.studenterror_set.all = mock.Mock(return_value=update)

        union_merge(tmp_user, user)
        self.assertEqual(tmp_user.role_set.all.call_count, 1)
        self.assertEqual(user.role_set.filter.call_count, 3)
        self.assertEqual(save.call_count, 5)

        self.assertEqual(update.update.call_count, 3)
        calls = [mock.call(user=user),
                 mock.call(author=user),
                 mock.call(author=user)]
        update.update.assert_has_calls(calls, any_order=True)


class MailTest(TestCase):
    """
    Testing send_validation function.
    """
    def test_send_validation(self):
        with mock.patch('psa.mail.send_mail') as mocked:
            mocked.return_value = None
            strategy, backend, code = (mock.Mock(),
                                       mock.Mock(),
                                       mock.Mock())
            backend.name = 'google-oauth2'
            code.code = 'test_code'
            code.email = 'test@test.com'
            self.assertIsNone(send_validation(strategy, backend, code))


class ValidatedUserDetailTest(TestCase):
    """
    Tests for ValidatedUserDetailTest.
    """
    def setUp(self):
        self.strategy = mock.Mock()
        self.backend = mock.Mock()
        self.details = {'email': 'test@test.com', 'username': 'new_username'}
        self.user = mock.Mock()
        self.user.username = 'anonymous'
        self.exists = mock.Mock()
        self.exists.exists.return_value = True
        self.user.groups.filter.return_value = self.exists
        self.social = mock.Mock()

    def test_temporary_user_with_social(self):
        self.social.user = mock.Mock()

        with mock.patch('psa.pipeline.logout') as mocked_logout:
            with mock.patch('psa.pipeline.login') as mocked_login:
                with mock.patch('psa.pipeline.union_merge') as mocked_merge:
                    mocked_logout.return_value = None
                    mocked_login.return_value = None
                    mocked_merge.return_value = None
                    res = validated_user_details(
                        strategy=self.strategy,
                        pipeline_index=6,
                        backend=self.backend,
                        details=self.details,
                        user=self.user,
                        social=self.social
                    )
                    self.assertEqual(res['user'], self.social.user)

    def test_temporary_user_without_social_user_by_email(self):
        user_by_email = mock.Mock()
        self.backend.strategy.storage.user.get_users_by_email.return_value = [user_by_email]
        self.details = {'email': 'test@test.com'}

        with mock.patch('psa.pipeline.logout') as mocked_logout:
            with mock.patch('psa.pipeline.login') as mocked_login:
                with mock.patch('psa.pipeline.union_merge') as mocked_merge:
                    mocked_logout.return_value = None
                    mocked_login.return_value = None
                    mocked_merge.return_value = None
                    res = validated_user_details(
                        strategy=self.strategy,
                        pipeline_index=6,
                        backend=self.backend,
                        details=self.details,
                        user=self.user
                    )
                    self.assertEqual(res['user'], user_by_email)

    def test_temporary_user_without_social_no_user_by_email(self):
        self.backend.strategy.storage.user.get_users_by_email.return_value = []

        with mock.patch('psa.pipeline.logout') as mocked_logout:
            with mock.patch('psa.pipeline.login') as mocked_login:
                with mock.patch('psa.pipeline.union_merge') as mocked_merge:
                    mocked_logout.return_value = None
                    mocked_login.return_value = None
                    mocked_merge.return_value = None
                    res = validated_user_details(
                        strategy=self.strategy,
                        pipeline_index=6,
                        backend=self.backend,
                        details=self.details,
                        user=self.user
                    )
                    self.assertEqual(res, {})
                    self.assertEqual(self.user.username, self.details.get('username'))
                    self.assertEqual(self.user.first_name, '')

    def test_temporary_user_without_social_two_user_by_email(self):
        self.backend.strategy.storage.user.get_users_by_email.return_value = [mock.Mock(),
                                                                              mock.Mock()]
        with mock.patch('psa.pipeline.logout') as mocked_logout:
            with mock.patch('psa.pipeline.login') as mocked_login:
                with mock.patch('psa.pipeline.union_merge') as mocked_merge:
                    mocked_logout.return_value = None
                    mocked_login.return_value = None
                    mocked_merge.return_value = None
                    with self.assertRaises(AuthException):
                        validated_user_details(
                            strategy=self.strategy,
                            pipeline_index=6,
                            backend=self.backend,
                            details=self.details,
                            user=self.user
                        )

    def test_integrity_error(self):
        self.backend.strategy.storage.user.get_users_by_email.return_value = []
        save = mock.Mock()
        save.side_effect = IntegrityError()
        self.user.save = save

        # pipeline do not raise IntegrityError but we mock user.save()
        # so in our test second call to save will raise IntegrityError
        # exception
        with self.assertRaises(IntegrityError):
            validated_user_details(
                strategy=self.strategy,
                pipeline_index=6,
                backend=self.backend,
                details=self.details,
                user=self.user
            )
            self.assertIn(self.details.get('username'), self.user.username)
            self.assertLess(len(self.details.get('username')),
                            len(self.user.username))

    def test_valid_user_with_social_confirm_no(self):
        self.social.user = mock.Mock()
        self.user.username = 'test_username'
        self.exists.exists.return_value = False
        self.strategy.request.POST = {'confirm': 'no'}

        with self.assertRaises(AuthException):
            validated_user_details(
                strategy=self.strategy,
                pipeline_index=6,
                backend=self.backend,
                details=self.details,
                user=self.user,
                social=self.social
            )

    def test_valid_user_with_social_confirm_yes(self):
        self.exists.exists.return_value = False

        self.social.user = mock.Mock()
        self.social.user.groups.filter.return_value = self.exists
        self.social.user.email = 'test@test.com'
        self.user.username = 'test_username'
        self.user.email = 'test@test.com'
        self.user.groups.filter.return_value = self.exists
        self.user.get_full_name.return_value = 'test_username1'
        self.social.user.get_full_name.return_value = 'test_username2'
        self.strategy.request.POST = {'confirm': 'yes'}

        with mock.patch('psa.pipeline.social_merge') as mocked_social:
            with mock.patch('psa.pipeline.union_merge') as mocked_union:
                mocked_social.return_value = None
                mocked_union.return_value = None
                res = validated_user_details(
                    strategy=self.strategy,
                    pipeline_index=6,
                    backend=self.backend,
                    details=self.details,
                    user=self.user,
                    social=self.social
                )
                self.assertEqual(res['user'], self.user)
                self.assertEqual(res['social'], self.social)

    def test_valid_user_with_social_without_confirm(self):
        self.exists.exists.return_value = False

        self.social.user = mock.Mock()
        self.social.user.groups.filter.return_value = self.exists
        self.social.user.email = 'test@test.com'
        self.user.groups.filter.return_value = self.exists
        self.user.username = 'test_username'
        self.user.email = 'test@test.com'
        self.user.get_full_name.return_value = 'test_username1'
        self.social.user.get_full_name.return_value = 'test_username2'
        self.strategy.request.POST = {}

        with mock.patch('psa.pipeline.social_merge') as mocked_social:
            with mock.patch('psa.pipeline.union_merge') as mocked_union:
                mocked_social.return_value = None
                mocked_union.return_value = None
                validated_user_details(
                    strategy=self.strategy,
                    pipeline_index=6,
                    backend=self.backend,
                    details=self.details,
                    user=self.user,
                    social=self.social
                )
                self.assertTemplateUsed('ct/person.html')


class CustomMailValidation(TestCase):
    """
    Testing psa.pipeline.custom_mail_validation.
    """
    def setUp(self):
        self.strategy = mock.Mock()
        self.backend = mock.Mock()
        self.backend.name = 'email'
        self.backend.setting.return_value = True
        self.backend.strategy.session_set = mock.Mock()
        self.backend.strategy.session_pop = mock.Mock()
        self.backend.strategy.request_data.return_value = {'verification_code': 'test_code'}
        self.details = {'email': 'test@test.com', 'username': 'new_username'}
        self.user = mock.Mock()
        self.social = mock.Mock()

    def test_custom_mail_validation_backend_not_email(self):
        self.backend.name = 'facebook'
        res = custom_mail_validation(
            strategy=self.strategy,
            pipeline_index=5,
            backend=self.backend,
            details=self.details,
            user=self.user,
            social=self.social
        )
        self.assertEqual(res, {})

    def test_custom_mail_validation_backend_email_verify_code(self):
        self.backend.strategy.validate_email.return_value = True
        code = mock.Mock()
        code.user_id = 1
        self.backend.strategy.storage.code.get_code.return_value = code

        with mock.patch('psa.pipeline.User') as mocked_user:
            with mock.patch('psa.pipeline.logout') as mocked_logout:
                with mock.patch('psa.pipeline.login') as mocked_login:
                    mocked_logout.return_value = None
                    mocked_login.return_value = None
                    queryset = mock.Mock()
                    queryset.first.return_value = self.user
                    mocked_user.objects.filter.return_value = queryset
                    res = custom_mail_validation(
                        strategy=self.strategy,
                        pipeline_index=5,
                        backend=self.backend,
                        details=self.details,
                        user=self.user
                    )
                    self.assertEqual(res['user'], self.user)
                    self.assertEqual(
                        self.user.backend,
                        'django.contrib.auth.backends.ModelBackend'
                    )

    def test_custom_mail_validation_raise(self):
        self.backend.strategy.validate_email.return_value = False
        with self.assertRaises(InvalidEmail):
            custom_mail_validation(
                strategy=self.strategy,
                pipeline_index=5,
                backend=self.backend,
                details=self.details,
                user=self.user
            )

    def test_custom_mail_validation_backend_email_send_email(self):
        self.backend.strategy.request_data.return_value = {}
        self.backend.strategy.send_email_validation = mock.Mock()
        self.user.username = 'test_user'
        exists = mock.Mock()
        exists.exists.return_value = False
        self.user.groups.filter.return_value = exists
        res = custom_mail_validation(
            strategy=self.strategy,
            pipeline_index=5,
            backend=self.backend,
            details=self.details,
            user=self.user
        )
        self.assertEqual(res, self.backend.strategy.redirect())

    def test_custom_mail_validation_backend_email_send_email_anonym(self):
        self.backend.strategy.request_data.return_value = {}
        send_email_validation = mock.Mock()
        self.backend.strategy.send_email_validation = send_email_validation
        self.user.username = 'anonymous_username'
        exists = mock.Mock()
        exists.exists.return_value = True
        self.user.groups.filter.return_value = exists
        with mock.patch('psa.pipeline.AnonymEmail') as mocked_anonym:
            get_or_create = mock.Mock()
            mocked_anonym.objects.get_or_create = get_or_create
            res = custom_mail_validation(
                strategy=self.strategy,
                pipeline_index=5,
                backend=self.backend,
                details=self.details,
                user=self.user
            )
            self.assertEqual(res, self.backend.strategy.redirect())
            self.assertEqual(get_or_create.call_count, 1)
            self.assertEqual(send_email_validation.call_count, 1)


@mock.patch('psa.custom_backends.CustomCode')
class EmailAuthTest(TestCase):
    """
    Testing EmailAuth.auth_complete method.
    """
    def setUp(self):
        self.test_email = 'test@test.com'
        self.email_auth = EmailAuth()
        self.email_auth.strategy = mock.Mock()
        self.email_auth.strategy.request.GET.get.return_value = True

        code_object = mock.Mock()
        code_object.email = self.test_email
        self.first = mock.Mock()
        self.first.first.return_value = code_object

    def test_update_email_from_code_custom_code_found(self, code):
        code.objects.filter.return_value = self.first
        self.email_auth.auth_complete()
        self.assertEqual(self.email_auth.data.get('email'), self.test_email)

    def test_update_email_from_code_no_custom_code_found(self, code):
        self.first = mock.Mock()
        self.first.first.return_value = None
        code.objects.filter.return_value = self.first
        with self.assertRaises(AuthMissingParameter):
            self.email_auth.auth_complete()


class SignupTest(TestCase):
    """
    Tests that psa.views.signup function works correctly
    """
    def setUp(self):
        self.url = reverse('signup')
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()  # we need to make load() work, or the cookie is worthless
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key

    def test_signup_logout(self):
        User.objects.create_user('test_user', 'test@aa.cc', '123')
        self.client.login(email='test@aa.cc', password='123')
        response = self.client.get(self.url)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_signup_with_u_hash_in_session(self):
        u_hash = uuid4().hex
        self.client.logout()

        session = self.client.session
        session.update({'u_hash': u_hash})
        session.save()

        self.assertEqual(CustomCode.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Instructor.objects.count(), 0)

        response = self.client.post(
            self.url,
            {
                'u_hash': u_hash,
                'email': 'test_email@aa.cc',
                'email_confirmation': 'test_email@aa.cc',
                'last_name': 'Bo',
                'first_name': 'Alex',
                'institution': 'testInstitute',
                'password': '123123123'
            },
            follow=True
        )
        self.assertRedirects(response, reverse('ctms:shared_courses'))
        self.assertIn('_auth_user_id', self.client.session)

        new_user = User.objects.get(email='test_email@aa.cc')

        self.assertEqual(int(self.client.session['_auth_user_id']), new_user.pk)
        self.assertEqual(CustomCode.objects.count(), 0)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Instructor.objects.count(), 1)

    def test_post_signup_form_invalid(self):
        response = self.client.post(
            self.url,
            {
                'email': 'test_email@aa.cc',
                'email_confirmation': 'test_email2222@aa.cc',
                'last_name': 'Bo',
                'first_name': 'Alex',
                'institution': '',
                'password': '123123123'
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn(u'Confirmation e-mail should be the same as e-mail.',
                      response.context['form']['email_confirmation'].errors)
        self.assertIn(u'This field is required.',
                      response.context['form']['institution'].errors)

    def test_signup_without_u_hash(self):
        self.assertEqual(CustomCode.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Instructor.objects.count(), 0)

        response = self.client.post(
            self.url,
            {
                'email': 'test_email@aa.cc',
                'email_confirmation': 'test_email@aa.cc',
                'last_name': 'Bo',
                'first_name': 'Alex',
                'institution': 'testInstitute',
                'password': '123123123'
            },
            follow=True
        )

        self.assertEqual(CustomCode.objects.count(), 1)
        self.assertEqual(User.objects.count(), 0)

        self.assertIn('resend_user_email', self.client.session)
        self.assertEqual(self.client.session['resend_user_email'], 'test_email@aa.cc')

        code = CustomCode.objects.all().first()
        print code

    def test_twitter_signup_anonymous_user_cancel(self):
        """Test when anonymous user cancel auth thought twitter should not see 500 error."""
        url = "/complete/twitter/?redirect_state=T6zv6SbT2HnhWxLExv1bSrTdcvFMcOMi&denied=06OETwAAAAAAexJsAAABY7v2Lig"
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('new_login') + "?next=/ctms/")
        self.assertTemplateUsed(response, 'psa/new_custom_login.html')

    def test_twitter_signup_loggedin_user_cancel(self):
        """Test when logged in user cancel auth thought twitter should not see 500 error."""
        User.objects.create_user(username='test', email='test@aa.cc', password='123')
        self.client.login(username='test', password='123')
        url = "/complete/twitter/?redirect_state=T6zv6SbT2HnhWxLExv1bSrTdcvFMcOMi&denied=06OETwAAAAAAexJsAAABY7v2Lig"
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('accounts:settings'))
        self.assertTemplateUsed(response, 'accounts/settings.html')


class LogoutTest(TestCase):
    def setUp(self):
        self.url = reverse('signup')
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()  # we need to make load() work, or the cookie is worthless
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key

    def test_logout(self):
        """Test that old logout page redirect to ct page after logout."""
        response = self.client.get(reverse('logout'), follow=True)
        self.assertRedirects(response, reverse('login'))
        self.assertEqual(self.client.cookies.get('sessionid').value, '')


    def test_new_logout(self):
        response = self.client.get(reverse('new_logout'), follow=True)
        self.assertRedirects(response, reverse('new_login')+'?next='+reverse('ctms:my_courses'))
        self.assertEqual(self.client.cookies.get('sessionid').value, '')
