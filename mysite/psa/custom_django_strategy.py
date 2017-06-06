"""Custom Strategy to implement handling user_id attr in Code object"""
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

from social.strategies.django_strategy import DjangoStrategy
from accounts.models import Instructor
from psa.custom_django_storage import CustomCode


class CustomDjangoStrategy(DjangoStrategy):
    """Custom DjangoStrategy

    Needed to add custom login and fix different session issue.
    """
    user_needed_fields = (
        'email',
        'first_name',
        'last_name',
        'password'
    )

    data_from_code_fields = user_needed_fields + ('institution',)

    def check_username_and_create_user(self, username, **kwargs):
        already_exists = User.objects.filter(
            username=username
        )
        if not already_exists:
            kwargs = self.clean_create_user_kwargs(**kwargs)
            data = dict(
                username=username,
                first_name=kwargs.get('first_name', ''),
                last_name=kwargs.get('last_name', ''),
            )
            data.update(kwargs)
            user = self.storage.user.create_user(**data)
            user.password = data['password']
            user.save()
            return user
        else:
            username += '_'
            return self.check_username_and_create_user(username, **kwargs)

    def clean_create_user_kwargs(self, **kwargs):
        return dict([(f, v) for f, v in kwargs.items() if f in self.user_needed_fields])

    def has_all_needed_fields(self, **kwargs):
        return all(f in kwargs for f in self.data_from_code_fields)

    def get_data_from_code(self, **kwargs):
        code = CustomCode.objects.filter(email=kwargs.get('email')).first()
        if code:
            return {f: getattr(code, f, '') for f in self.data_from_code_fields}
        return {}

    def create_user(self, *args, **kwargs):
        if self.has_all_needed_fields(**kwargs):
            data = kwargs
        else:
            data = self.get_data_from_code(**kwargs)

        username = data.pop('username', None)
        if not username:
            username = data.get('email', '').split('@')[0]

        user = self.check_username_and_create_user(username, **data)
        Instructor.objects.create(
            user=user,
            institution=data.get('institution', ''),
        )
        return user

    def send_email_validation(self, backend, email, force_update=False):
        code = super(CustomDjangoStrategy, self).send_email_validation(backend, email)
        user = self.request.user
        # store user data in code. We will use it after confirmation email link click.
        fields_to_store = ('institution', 'first_name', 'last_name', 'password')
        for field in fields_to_store:
            f_val = self.request.POST.get(field)
            setattr(
                code, field,
                f_val if field != 'password' else make_password(f_val)
            )
        if user and user.is_authenticated():
            code.force_update = force_update
            code.user_id = user.id
        code.save()
        return code
