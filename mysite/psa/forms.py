from django import forms
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

from accounts.models import Instructor
from psa.custom_django_storage import CustomCode
from psa.models import SecondaryEmail

PASSWORD_MIN_CHARS = 6
password_validator = RegexValidator(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{%s,}$' % (PASSWORD_MIN_CHARS,),
    message="Password should contain minimum 6 chars with 1 capital char and 1 digit char.")

class SignUpForm(forms.Form):
    """
    This form handles and validate data for signup process.
    """
    next = forms.CharField(widget=forms.HiddenInput(), required=False)
    email = forms.EmailField()
    email_confirmation = forms.EmailField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    institution = forms.CharField()
    password = forms.CharField(
        widget=forms.PasswordInput(), min_length=6,
        validators=[password_validator]
    )

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
        if User.objects.filter(email=email) or CustomCode.objects.filter(email=email, verified=True):
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


class SocialForm(forms.ModelForm):
    class Meta:
        model = Instructor
        fields = (
            'user',
            'institution',
            'id',
        )
        widgets = {
            'user': forms.HiddenInput(),
            'id': forms.HiddenInput(),

        }
