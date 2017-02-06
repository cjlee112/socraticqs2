from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth.models import User

from accounts.models import Instructor
from psa.custom_django_storage import CustomCode


class AccountSettingsTests(TestCase):
    def setUp(self):
        self.url = reverse('accounts:settings')
        self.user = User.objects.create_user(
            username='username',
            email='email@mail.com',
            password='123'
        )
        self.instructor = Instructor(user=self.user)
        self.instructor.save()
        self.client.login(username='username', password='123')

    def get_user(self):
        return User.objects.get(id=self.user.id)

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('login')+'?next='+self.url)

    def test_get_account_settings_page(self):
        self.client.login(username='username', password='123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/settings.html')
        self.assertIn('user_form', response.context)
        self.assertIn('instructor_form', response.context)
        self.assertIn('password_form', response.context)
        self.assertIn('delete_account_form', response.context)
        self.assertIn('email_form', response.context)
        self.assertIn('person', response.context)

        self.assertEqual(response.context['user_form'].instance, self.user)
        self.assertEqual(response.context['email_form'].initial['email'], self.user.email)
        self.assertEqual(response.context['instructor_form'].instance, self.user.instructor)
        self.assertEqual(response.context['delete_account_form'].instance, self.user)
        self.assertEqual(response.context['person'], self.user)

    def test_post_valid_change_user_data(self):
        data = {'first_name': 'SomeUser', 'last_name': 'somesome', 'form_id': 'user_form'}
        response = self.client.post(self.url, data, follow=True)
        user = self.get_user()
        self.assertRedirects(response, self.url)
        self.assertEqual(user.first_name, 'SomeUser')
        self.assertEqual(user.last_name, 'somesome')

    def test_post_valid_institution(self):
        data = {'institution': 'SomeInstitute', 'user': self.user.id, 'form_id': 'instructor_form'}
        response = self.client.post(self.url, data, follow=True)
        instructor = Instructor.objects.get(user__id=self.user.id)
        self.assertRedirects(response, self.url)
        self.assertEqual(instructor.institution, 'SomeInstitute')

    def test_post_valid_password_change(self):
        data = {'confirm_password': '1234', 'password': '1234', 'form_id': 'password_form'}
        response = self.client.post(self.url, data, follow=True)
        self.assertRedirects(response, self.url)
        can_login = self.client.login(username='username', password='1234')
        self.assertTrue(can_login)

    def test_post_valid_email_change(self):
        data = {'email': 'mm@mail.com', 'form_id': 'email_form'}
        response = self.client.post(self.url, data, follow=True)
        self.assertRedirects(response, self.url)
        cc = CustomCode.objects.all().last()
        self.assertEqual(cc.email, data['email'])
        self.assertEqual(cc.user_id, self.user.id)
        self.assertEqual(cc.verified, False)

        user = self.get_user()
        self.assertEqual(user.email, self.user.email)

        response = self.client.get(
            "/complete/email/?verification_code={}".format(cc.code)
        )
        user = self.get_user()
        self.assertEqual(user.email, 'mm@mail.com')
        self.assertRedirects(response)


class DeleteAcountTests(AccountSettingsTests):
    def test_post_valid_data(self):
        data = {'confirm_delete_account': True, 'form_id': 'delete_account_form'}
        response = self.client.post(reverse('accounts:delete'), data)
        user = self.get_user()
        self.assertNotEqual(user.is_active, self.user.is_active)
        self.assertRedirects(response, reverse('accounts:deleted'))

    def test_post_invalid_data(self):
        data = {'confirm_delete_account': False}
        response = self.client.post(reverse('accounts:delete'), data)
        user = self.get_user()
        # user not deleted
        self.assertEqual(user.is_active, self.user.is_active)
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'accounts/settings.html')
        self.assertTrue(bool(response.context['delete_account_form'].errors))
