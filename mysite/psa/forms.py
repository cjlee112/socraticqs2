from django import forms
from django.contrib.auth.models import User
from psa.custom_django_storage import CustomCode
from psa.models import SecondaryEmail


class SignUpForm(forms.Form):
    '''Fields to handle on:
        Email
        Re-enter email
        First name
        Last name
        Institution
        Password'''
    next = forms.CharField(widget=forms.HiddenInput(), required=False)
    email = forms.EmailField()
    email_confirmation = forms.EmailField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    institution = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        confirm_email = self.cleaned_data.get('email_confirmation')
        email = self.cleaned_data.get('email')
        if confirm_email and email and email == confirm_email:
            return self.cleaned_data
        else:
            self._errors['email_confirmation'] = 'Should be the same as email'
            raise forms.ValidationError(
                "Fields {} and {} should have the same values".format(
                    'email',
                    'email confirmation')
            )

    def clean_email(self):
        email = self.cleaned_data['email']
        already_exists_exc = forms.ValidationError('This email is already registered in the system.')
        if User.objects.filter(email=email):
            raise already_exists_exc
        if CustomCode.objects.filter(email=email, verified=True):
            raise already_exists_exc
        return email


class EmailLoginForm(forms.Form):
    next = forms.CharField(required=False, widget=forms.HiddenInput())
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())

class UsernameLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())
    next = forms.CharField(required=False, widget=forms.HiddenInput())
