import uuid
from unittest import TestCase

import pytest
from django.contrib.auth.models import User
from social_django.models import UserSocialAuth

from accounts.models import Instructor
from psa.forms import SignUpForm, CompleteEmailForm, EmailLoginForm, UsernameLoginForm
from psa.models import SecondaryEmail


@pytest.mark.django_db
class BaseFormMixin(object):
    """This class is NO A TEST."""
    form_cls = SignUpForm  # as example
    valid_test_data = {
        'email': 'aa@cc.com'  # example
    }
    not_valid_test_data = [
        {'email': ''}  # example
    ]

    def setUp(self):
        super(BaseFormMixin, self).setUp()
        self.user = User.objects.create_user(username='test', email='123@aa.cc', password='123123123')
        provider = UserSocialAuth.objects.create(user=self.user, provider='email', uid='ewfwfwefwef')
        SecondaryEmail.objects.create(user=self.user, provider=provider, email='123@aa.com')

    def test_form_valid(self):
        if isinstance(self.valid_test_data, (list, tuple)):
            for data in self.valid_test_data:
                form = self.form_cls(data=data)
                self.assertTrue(form.is_valid())
        else:
            form = self.form_cls(data=self.valid_test_data)
            self.assertTrue(form.is_valid())

        not_valid = getattr(self, 'not_valid_test_data', [])
        if not_valid and isinstance(not_valid, (list, tuple)):
            for data in not_valid:
                form = self.form_cls(data=data)
                self.assertFalse(form.is_valid())
        else:
            form = self.form_cls(data=not_valid)
            self.assertFalse(form.is_valid())


@pytest.mark.django_db
class SignUpFormTest(BaseFormMixin, TestCase):
    form_cls = SignUpForm
    valid_test_data = [
        {
            'email': '1234@aa.cc',
            'email_confirmation': '1234@aa.cc',
            'first_name': 'Ale',
            'last_name': 'Bo',
            'institution': 'KTUR',
            'password': '123123123'
        },
    ]
    not_valid_test_data = [
        {
            # email and confirm_email are not equal
            'email': '1234@aa.ccom',
            'email_confirmation': '1234@aa.cc',
            'first_name': 'Ale',
            'last_name': 'Bo',
            'institution': 'KTUR',
            'password': '123123123'

        },
        {
            # first name and last names are required
            'email': '1234@aa.cc',
            'email_confirmation': '1234@aa.cc',
            'first_name': '',
            'last_name': '',
            'institution': 'KTUR',
            'password': '123123123'
        },
        {
            # institution is required
            'email': '1234@aa.cc',
            'email_confirmation': '1234@aa.cc',
            'first_name': 'Ale',
            'last_name': 'Bo',
            'institution': '',
            'password': '123123123'

        },
        {
            # pw is required
            'email': '1234@aa.cc',
            'email_confirmation': '1234@aa.cc',
            'first_name': 'Ale',
            'last_name': 'Bo',
            'institution': 'KTUR',
            'password': ''
        },
        {
            # email alresdy taken
            'email': '123@aa.cc',
            'email_confirmation': '123@aa.cc',
            'first_name': 'Ale',
            'last_name': 'Bo',
            'institution': 'KTUR',
            'password': '123123123'
        }
    ]




@pytest.mark.django_db
class CompleteEmailFormTest(BaseFormMixin, TestCase):
    form_cls = CompleteEmailForm
    valid_test_data = {
        'email': '123@aq.cc'
    }
    not_valid_test_data = {
        'email': '123.cpm'
    }




@pytest.mark.django_db
class EmailLoginFormTest(BaseFormMixin, TestCase):
    form_cls = EmailLoginForm
    valid_test_data = [
        {   # test get_user and that next and has are not required
            'email': '123@aa.cc',
            'password': '123123123'
        },
        {   # check that all fields validates correctly and get_user work too
            'next': '/ctms/',
            'hash': uuid.uuid4().hex,
            'email': '123@aa.cc',
            'password': '123123123',
        },
        {   # secondary email test
            'email': '123@aa.com',
            'password': '123123123',
        }
    ]
    not_valid_test_data = [
        {
            # email not correct
            'email': '123aa.com',
            'password': '123123123',
        },
        {
            # no pw
            'email': '123@aa.com',
            'password': '',
        }
    ]

    def test_get_user(self):
        form = self.form_cls(data=self.valid_test_data[0])
        self.assertTrue(form.is_valid())
        user = form.get_user()
        self.assertEqual(user.email, self.valid_test_data[0]['email'])
        self.assertIsNotNone(Instructor.objects.filter(user=user).first())


@pytest.mark.django_db
class UsernameLoginFormTest(BaseFormMixin, TestCase):
    form_cls = UsernameLoginForm
    valid_test_data = [
        {  # test get_user and that next and has are not required
            'username': 'test',
            'password': '123123123'
        },
        {  # check that all fields validates correctly and get_user work too
            'next': '/ctms/',
            'username': 'test',
            'password': '123123123',
        },
    ]
    not_valid_test_data = [
        {
            # no pw
            'username': 'test',
            'password': '',
        },
        {
            # no username
            'username': '',
            'password': '123123123',
        }
    ]

    def test_get_user(self):
        form = self.form_cls(data={
            # username not correct - no such user
            'username': 'test1',
            'password': '123123123',
        })
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.get_user())
