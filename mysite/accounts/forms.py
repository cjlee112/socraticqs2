from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.db.models import Q
from django.contrib.auth.models import User
from social.apps.django_app.views import complete

from accounts.models import Instructor
from psa.models import SecondaryEmail


class UserForm(forms.ModelForm):
    '''
    This form allow user to edit his profile.
    On profile page there are a couple of forms with required fields.
    Field form_id is here to check what form was submitted.
    In view: If we found that form_id is present in request.POST we pass POST data to this form and validate it.
    If form_id not found in request.POST we will not validate this form.
    '''
    form_id = forms.CharField(max_length=255, initial='user_form', widget=forms.HiddenInput())

    class Meta:
        model = User
        fields = ('form_id', 'first_name', 'last_name')
        widgets = {
            'id': forms.HiddenInput(),
            'form_id': forms.HiddenInput(),
        }


class ChangeEmailForm(forms.Form):
    '''
    Field form_id is here to check what form was submitted.
    In view: If we found that form_id is present in request.POST we pass POST data to this form and validate it.
    If form_id not found in request.POST we will not validate this form.
    '''
    form_id = forms.CharField(max_length=255, initial='email_form', widget=forms.HiddenInput())
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data['email']
        my_email = self.initial['email']
        if 'email' in self.changed_data:
            already_taken = User.objects.filter(
                Q(email=email) | Q(secondary__email=email)
            ).exclude(email=my_email)
            if already_taken:
                raise forms.ValidationError('This email already taken.')
        return email

    def save(self, request, commit=True):
        '''
        This form calls to `complete` function of python-social-auth
        to send email to the user with confirmation link when user changes his email.
        :param request: django request
        :param commit: save to db or not?
        :return:
        '''
        if self.initial['email'] != self.cleaned_data['email']:
            complete(request, 'email', force_update=True)
            return True
        return False


class InstructorForm(forms.ModelForm):
    '''
    Field form_id is here to check what form was submitted.
    In view: If we found that form_id is present in request.POST we pass POST data to this form and validate it.
    If form_id not found in request.POST we will not validate this form.
    '''
    form_id = forms.CharField(max_length=255, initial='instructor_form', widget=forms.HiddenInput())

    class Meta:
        model = Instructor
        fields = ('form_id', 'user', 'institution')
        widgets = {
            'user': forms.HiddenInput(),
            'form_id': forms.HiddenInput(),
        }

class ChangePasswordForm(forms.ModelForm):
    '''
    Field form_id is here to check what form was submitted.
    In view: If we found that form_id is present in request.POST we pass POST data to this form and validate it.
    If form_id not found in request.POST we will not validate this form.
    '''
    form_id = forms.CharField(max_length=255, initial='password_form', widget=forms.HiddenInput())
    confirm_password = forms.CharField(max_length=255, widget=forms.PasswordInput())
    password = forms.CharField(max_length=255, widget=forms.PasswordInput())

    def clean(self):
        data = self.cleaned_data
        if data.get('password') != data.get('confirm_password'):
            raise forms.ValidationError(
                'Password and Confirm password fields doesn\'t match'
            )
        return self.cleaned_data

    class Meta:
        model = User
        fields = ('password', 'confirm_password')

    def save(self, commit=True):
        self.instance.set_password(self.cleaned_data['password'])
        if commit:
            self.instance.save()
        return self.instance


class DeleteAccountForm(forms.ModelForm):
    '''
    Field form_id is here to check what form was submitted.
    In view: If we found that form_id is present in request.POST we pass POST data to this form and validate it.
    If form_id not found in request.POST we will not validate this form.
    '''
    form_id = forms.CharField(max_length=255, initial='delete_account_form', widget=forms.HiddenInput())
    confirm_delete_account = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(),
        initial=False
    )

    def save(self, commit=True):
        self.instance.is_active = False
        if commit:
            self.instance.save()
        return self.instance

    class Meta:
        model = User
        fields = ('form_id', 'confirm_delete_account')
        widgets = {
            'id': forms.HiddenInput(),
        }


class CustomPasswordResetForm(PasswordResetForm):
    '''
    Field form_id is here to check what form was submitted.
    In view: If we found that form_id is present in request.POST we pass POST data to this form and validate it.
    If form_id not found in request.POST we will not validate this form.
    '''

    def clean_email(self):
        if not User.objects.filter(email=self.cleaned_data['email']):
            raise forms.ValidationError('No registered account with such email.')
        return self.cleaned_data['email']