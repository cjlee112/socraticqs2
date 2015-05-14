import mock
from django.http import HttpResponse
from django.test import TestCase, Client
from django.test.client import RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from social.exceptions import AuthAlreadyAssociated, AuthException

from psa.views import (context,
                       validation_sent,
                       custom_login,
                       done,
                       ask_stranger)
from psa.pipeline import (social_user,
                          not_allowed_to_merge,
                          associate_user,
                          associate_by_email,
                          social_merge,
                          union_merge)


class ViewsUnitTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/login/')
        self.client = Client()
        self.client.get('/login/')
        self.request.session = self.client.session
        self.request.session['email_validation_address'] = 'test@test.com'

    def test_context(self):
        """Need to return avaliable_backends variable"""
        result = context()
        self.assertTrue('available_backends' in result)

    def test_validation_sent(self):
        anonymous = AnonymousUser()
        self.request.user = anonymous
        response = validation_sent(self.request)
        self.assertIsInstance(response, HttpResponse)
        self.assertTrue('test@test.com' in response.content)

    def test_custom_login_get(self):
        response = custom_login(self.request)
        self.assertIsInstance(response, HttpResponse)
        self.assertTrue('LoginForm' in response.content)

    def test_custom_login_post_negative(self):
        self.client = Client()
        credentials = {'username': 'test',
                       'password': 'test'}
        response = self.client.post('/login/', data=credentials)
        self.assertTemplateUsed(response, template_name='psa/custom_login.html')

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

    def test_done(self):
        user = User(username='test_user')
        user.set_password('test')
        user.save()
        self.request.user = user
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
        response = self.client.post('/set-pass/',
                                    data=credentials_for_set_pass,
                                    follow=True)
        self.assertTemplateUsed(response, template_name='ct/person.html')
        self.assertTrue('Your password was changed' in response.content)
        user = User.objects.get(username='test')
        self.assertTrue(user.check_password('test2'))


class TestSocialUser(TestCase):
    """Test for custom_mail_validation pipeline"""
    def setUp(self):
        self.user = User(username='test')
        self.main_user = User(username='main')
        self.social = mock.Mock()
        self.social.user = self.user
        self.anonymous = User(username='anonymous_test')

    def test_no_social(self):
        attrs = {'strategy.storage.user.get_social_auth.return_value': []}
        backend = mock.Mock(**attrs)
        backend.name = 'google-oauth2'
        uid = 'test@test.com'

        res = social_user(backend, uid)
        self.assertEqual(res['user'], None)
        self.assertEqual(res['social'], [])
        self.assertEqual(res['is_new'], True)
        self.assertEqual(res['new_association'], False)

    def test_social_stranger(self):
        attrs = {'strategy.storage.user.get_social_auth.return_value': self.social}
        backend = mock.Mock(**attrs)
        backend.name = 'google-oauth2'
        uid = 'test@test.com'

        res = social_user(backend, uid)
        self.assertEqual(res['user'], self.user)
        self.assertEqual(res['social'], self.social)
        self.assertEqual(res['is_new'], False)
        self.assertEqual(res['new_association'], False)

    def test_social_validated(self):
        attrs = {'strategy.storage.user.get_social_auth.return_value': self.social}
        backend = mock.Mock(**attrs)
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
        attrs = {'strategy.storage.user.get_social_auth.return_value': self.social}
        backend = mock.Mock(**attrs)
        backend.name = 'google-oauth2'
        uid = 'test@test.com'

        with mock.patch('psa.pipeline.not_allowed_to_merge') as mocked:
            mocked.return_value = True
            with self.assertRaises(AuthAlreadyAssociated):
                social_user(backend, uid, user=self.main_user)

    def test_social_anonymous(self):
        attrs = {'strategy.storage.user.get_social_auth.return_value': self.social}
        backend = mock.Mock(**attrs)
        backend.name = 'google-oauth2'
        uid = 'test@test.com'

        res = social_user(backend, uid, user=self.anonymous)
        self.assertEqual(res['user'], self.user)
        self.assertEqual(res['social'], self.social)
        self.assertEqual(res['is_new'], False)
        self.assertEqual(res['new_association'], False)


class NotAllowedToMergeTest(TestCase):
    """Test not_allowed_to_merge function"""
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
        self.user1.social_auth.all = mock.Mock(return_value=(self.provider1, self.provider2))
        self.user2.social_auth.all = mock.Mock(return_value=(self.provider3,))

        res = bool(not_allowed_to_merge(self.user1, self.user2))
        self.assertFalse(res)

    def test_not_allowed_to_merge_true(self):
        self.user1.social_auth.all = mock.Mock(return_value=(self.provider1, self.provider2))
        self.user2.social_auth.all = mock.Mock(return_value=(self.provider2, self.provider3))

        res = bool(not_allowed_to_merge(self.user1, self.user2))
        self.assertTrue(res)


class AssociateUserTest(TestCase):
    """Test for associate_user pipeline"""
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
            res = associate_user(self.backend, self.details, 'test@test.com', user=self.user)
            self.assertEqual(res['social'], self.social)
            self.assertEqual(res['user'], self.social.user)
            self.assertEqual(res['new_association'], True)

    def test_associate_user_raise_exception(self):
        create_sa = mock.Mock(side_effect=Exception())
        self.backend.strategy.storage.user.create_social_auth = create_sa
        self.backend.strategy.storage.is_integrity_error = mock.Mock(return_value=False)

        with self.assertRaises(Exception):
            associate_user(self.backend,
                           self.details,
                           'test@test.com',
                           user=self.user)

    def test_associate_user_handle_exception(self):
        create_sa = mock.Mock(side_effect=Exception())
        self.backend.strategy.storage.user.create_social_auth = create_sa
        self.backend.strategy.storage.is_integrity_error = mock.Mock(return_value=True)

        with mock.patch('psa.pipeline.social_user') as mocked:
            mocked.return_value = mock.Mock()
            res = associate_user(self.backend,
                                 self.details,
                                 'test@test.com',
                                 user=self.user)
            self.assertEqual(res, mocked.return_value)


class AssociateByEmailTest(TestCase):
    """Test associate_by_email pipeline"""
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
    """Test social_merge function"""
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
    """Test union_merge function"""
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
        for us in (unitstatus1, unitstatus2):
            us.save = save
        tmp_user.unitstatus_set.all = mock.Mock(return_value=(unitstatus1, unitstatus2))

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
        calls = [mock.call(user=user), mock.call(author=user), mock.call(author=user)]
        update.update.assert_has_calls(calls, any_order=True)
