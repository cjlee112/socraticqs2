from mock import patch
from django.test import TestCase, Client
from django.test.client import RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpResponse, HttpRequest

from psa.views import (context,
                       validation_sent,
                       custom_login,
                       done,
                       ask_stranger)


class MockRequest(object):
    method = 'GET'
    GET = {'REDIRECT_FIELD_NAME': '/ct'}


class MockSuperUser(object):
    def has_perm(self, perm):
        return True


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