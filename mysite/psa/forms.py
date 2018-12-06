from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.forms.utils import ErrorList

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
    u_hash = forms.CharField(widget=forms.HiddenInput(), required=False)

    email = forms.EmailField()
    email_confirmation = forms.EmailField()
    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Last name'}))
    password = forms.CharField(
        widget=forms.PasswordInput(), min_length=6,
        help_text='Choose a password that\'s at least six characters long.'
        # validators=[password_validator]
    )

    def clean(self):
        confirm_email = self.cleaned_data.get('email_confirmation')
        email = self.cleaned_data.get('email')
        if email and confirm_email and email == confirm_email:
            return self.cleaned_data
        else:
            err_field = 'email_confirmation'
            if confirm_email and not email:
                err_field = 'email'
            elif confirm_email and email and email != confirm_email:
                self.add_error('email', 'Confirmation e-mail and e-mail should be the same.')
            self.add_error(err_field, 'Confirmation e-mail should be the same as e-mail.')

    def clean_email(self):
        email = self.cleaned_data['email']
        already_exists_exc = forms.ValidationError('This email is already registered in the system.')
        if User.objects.filter(email=email) or CustomCode.objects.filter(email=email, verified=True):
            raise already_exists_exc
        return email


class CompleteEmailForm(forms.Form):
    email = forms.EmailField()


class EmailLoginForm(forms.Form):
    next = forms.CharField(required=False, widget=forms.HiddenInput())
    u_hash = forms.CharField(widget=forms.HiddenInput(), required=False)

    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        user = self.get_user()
        if user:
            return self.cleaned_data
        self.add_error('email', 'Provided credentials are not correct for this user.')

    def get_user(self):
        username = ''
        user = User.objects.filter(email=self.cleaned_data.get('email')).first()
        if not user:
            sec_mail = SecondaryEmail.objects.filter(
                email=self.cleaned_data.get('email')
            ).first()
            if sec_mail:
                user = sec_mail.user
        if user:
            username = user.username
        user = authenticate(username=username, password=self.cleaned_data.get('password'))
        if user and user.is_active:
            # create instructor if not exist
            Instructor.objects.get_or_create(user=user)
        return user


class UsernameLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())
    next = forms.CharField(required=False, widget=forms.HiddenInput())

    def get_user(self):
        return authenticate(username=self.cleaned_data.get('username'),
                            password=self.cleaned_data.get('password'))


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
