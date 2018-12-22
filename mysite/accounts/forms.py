from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.core.validators import MinLengthValidator
from django.db.models import Q
from django.contrib.auth.models import User
from social_django.views import complete

from accounts.models import Instructor


class UserForm(forms.ModelForm):
    """
    This form allow user to edit his profile.

    On profile page there are a couple of forms with required fields.
    Field form_id is here to check what form was submitted.
    In view: If we found that form_id is present in request.POST we pass POST data to this form and validate it.
    If form_id not found in request.POST we will not validate this form.
    """
    form_id = forms.CharField(max_length=255, initial='user_form', widget=forms.HiddenInput())

    class Meta:
        model = User
        fields = ('form_id', 'first_name', 'last_name')
        widgets = {
            'id': forms.HiddenInput(),
            'form_id': forms.HiddenInput(),
        }


class ChangeEmailForm(forms.Form):
    """
    Field form_id is here to check what form was submitted.

    In view: If we found that form_id is present in request.POST we pass POST data to this form and validate it.
    If form_id not found in request.POST we will not validate this form.
    """
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
        """
        This form calls to `complete` function of python-social-auth.

        Send email to the user with confirmation link when user changes his email.
        :param request: django request
        :param commit: save to db or not?
        :return:
        """
        if self.initial['email'] != self.cleaned_data['email']:
            return complete(request, 'email', force_update=True)


class InstructorForm(forms.ModelForm):
    """
    Field form_id is here to check what form was submitted.

    In view: If we found that form_id is present in request.POST we pass POST data to this form and validate it.
    If form_id not found in request.POST we will not validate this form.
    """
    form_id = forms.CharField(max_length=255, initial='instructor_form', widget=forms.HiddenInput())

    class Meta:
        model = Instructor
        fields = ('form_id', 'user', 'institution')
        widgets = {
            'user': forms.HiddenInput(),
            'form_id': forms.HiddenInput(),
        }


class CreatePasswordForm(forms.ModelForm):
    """This form will be used in case when user has no password and wants to create it."""

    form_id = forms.CharField(max_length=255, initial='password_form', widget=forms.HiddenInput())
    confirm_password = forms.CharField(max_length=255, widget=forms.PasswordInput())
    password = forms.CharField(max_length=255, widget=forms.PasswordInput())

    def clean(self):
        data = self.cleaned_data
        if data.get('password') != data.get('confirm_password'):
            self.add_error(None, 'Password and Confirm password fields doesn\'t match.')
            raise forms.ValidationError(
                {'password': 'Should be equal to confirm password field.',
                 'confirm_password': 'Should be equal to password field.'})
        return self.cleaned_data

    class Meta:
        model = User
        fields = ('password', 'confirm_password', 'form_id')

    def save(self, commit=True):
        self.instance.set_password(self.cleaned_data['password'])
        if commit:
            self.instance.save()
        return self.instance


class ChangePasswordForm(CreatePasswordForm):
    """
    Field form_id is here to check what form was submitted.

    In view: If we found that form_id is present in request.POST we pass POST data to this form and validate it.
    If form_id not found in request.POST we will not validate this form.
    """
    current_password = forms.CharField(max_length=255, widget=forms.PasswordInput())

    def clean(self):
        data = self.cleaned_data
        if data.get('password') != data.get('confirm_password'):
            self.add_error('password', 'Should be equal to confirm password field.')
            self.add_error('confirm_password', 'Should be equal to password field.')
            self.add_error(None, 'Password and Confirm password fields doesn\'t match.')
        return self.cleaned_data

    def clean_current_password(self):
        current_pw = self.cleaned_data.get('current_password')
        user = authenticate(username=self.instance, password=current_pw)
        if user is None:
            self.add_error('current_password', 'Provided current password doesn\'t match your password')
        return current_pw

    class Meta:
        model = User
        fields = ('current_password', 'password', 'confirm_password', 'form_id')


class DeleteAccountForm(forms.ModelForm):
    """
    Field form_id is here to check what form was submitted.

    In view: If we found that form_id is present in request.POST we pass POST data to this form and validate it.
    If form_id not found in request.POST we will not validate this form.
    """
    form_id = forms.CharField(max_length=255, initial='delete_account_form', widget=forms.HiddenInput())
    confirm_delete_account = forms.BooleanField(
        required=True,
        widget=forms.HiddenInput(),
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
    """
    Field form_id is here to check what form was submitted.

    In view: If we found that form_id is present in request.POST we pass POST data to this form and validate it.
    If form_id not found in request.POST we will not validate this form.
    """

    def clean_email(self):
        user = User.objects.filter(email=self.cleaned_data['email']).first()
        if not user:
            raise forms.ValidationError('No registered account with such email.')
        if not user.has_usable_password():
            raise forms.ValidationError(
                'User with this email does not have password, more likely you registered via social network')
        return self.cleaned_data['email']


class SocialForm(forms.ModelForm):
    institution = forms.CharField(required=True)
    what_do_you_teach = forms.CharField(required=True)

    class Meta:
        model = Instructor
        fields = (
            'user',
            'institution',
            'what_do_you_teach'
        )
        widgets = {
            'user': forms.HiddenInput(),

        }


class CustomSetPasswordForm(SetPasswordForm):

    def __init__(self, user, *args, **kwargs):
        super(CustomSetPasswordForm, self).__init__(user, *args, **kwargs)
        self.fields['new_password1'].validators.append(MinLengthValidator(6))
        self.fields['new_password2'].validators.append(MinLengthValidator(6))
