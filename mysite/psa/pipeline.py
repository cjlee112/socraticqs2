from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.conf import settings
from django.db import IntegrityError

from social.pipeline.partial import partial
from social.exceptions import InvalidEmail, AuthAlreadyAssociated
from ct.models import Role
from psa.models import AnonymEmail
from datetime import datetime


@partial
def password_ask(strategy, details, user=None, is_new=False, *args, **kwargs):
    if (is_new and kwargs.get('backend').name == 'email'):
        email = user.email or details.get('email')
        if strategy.request.POST.get('password'):
            if 'anonymous' in user.username:
                user.username = details.get('username')
                user.first_name = ''
            username = user.username
            password = strategy.request.POST.get('password')
            user.set_password(password)
            user.save()
            if email:
                send_mail('Account is created',
                          'Account is created.\nUsername: {0}\nPassword: {1}'.format(username,
                                                                                     password),
                          settings.EMAIL_FROM,
                          [email],
                          fail_silently=False)
        else:
            return render_to_response('psa/require_password.html', {
                'request': strategy.request,
                'next': strategy.request.POST.get('next') or ''
            }, RequestContext(strategy.request))


@partial
def custom_mail_validation(backend, details, user=None, is_new=False, *args, **kwargs):
    requires_validation = backend.REQUIRES_EMAIL_VALIDATION or \
                          backend.setting('FORCE_EMAIL_VALIDATION', False)
    send_validation = details.get('email') and \
                      (is_new or backend.setting('PASSWORDLESS', False))

    if requires_validation and send_validation and backend.name == 'email':
        data = backend.strategy.request_data()
        if 'verification_code' in data:
            backend.strategy.session_pop('email_validation_address')
            if not backend.strategy.validate_email(details['email'],
                                           data['verification_code']):
                raise InvalidEmail(backend)
        else:
            if user and 'anonymous' in user.username:
                AnonymEmail.objects.get_or_create(user=user, email=details.get('email'),
                                                  defaults={'date': datetime.now()})
            backend.strategy.send_email_validation(backend, details['email'])
            backend.strategy.session_set('email_validation_address',
                                         details['email'])
            return backend.strategy.redirect(
                backend.strategy.setting('EMAIL_VALIDATION_URL')
            )


def role_set(strategy, details, user=None, *args, **kwargs):
    if 'anonymous' in user.username:
        print('anonym_role_set')
        # user.role_set.all().update(user=user)


def validated_user_details(strategy, details, user=None, is_new=False, *args, **kwargs):
    if user and 'anonymous' in user.username:
        try:
            user.username = details.get('username')
            user.first_name = ''
            user.save()
        except IntegrityError as e:
            raise AuthAlreadyAssociated(kwargs.get('backend'), str(e))
