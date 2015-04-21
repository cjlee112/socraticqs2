from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db import IntegrityError
import time
from datetime import datetime, timedelta

from social.pipeline.partial import partial
from social.exceptions import InvalidEmail, AuthAlreadyAssociated

from social.apps.django_app.default.models import UserSocialAuth
from ct.models import Role, UnitStatus, FSMState, Response
from psa.models import AnonymEmail, SecondaryEmail


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


def union_merge(tmp_user, user):
    """
       Reassigning Roles
       Doing UNION megre to not repeat roles to the same course
       with the save role
    """
    roles_to_reset = (role for role in tmp_user.role_set.all()
                      if not user.role_set.filter(course=role.course,
                                                  role=role.role))
    for role in roles_to_reset:
        role.user = user
        role.save()
    """
       Reassigning UnitStatuses
       TODO think about filter() for UNION instead all()
       maybe we need fresh unitstatuses instead of all to reassing
    """
    unitstatus_to_reset = (us for us in tmp_user.unitstatus_set.all())
    for ut in unitstatus_to_reset:
        ut.user = user
        ut.save()
    """ Reassigning FSMStates """
    tmp_user.fsmstate_set.all().update(user=user)
    """ Reassigning Responses """
    tmp_user.response_set.all().update(author=user)
    """ Reassigning StudentErrors """
    tmp_user.studenterror_set.all().update(author=user)


def social_merge(tmp_user, user):
    tmp_user.social_auth.all().update(user=user)
    tmp_user.lti_auth.all().update(django_user=user)


def validated_user_details(strategy, details, user=None, is_new=False, *args, **kwargs):
    """Merge actions

    Make different merge actions based on user type.
    """
    social = kwargs.get('social')
    if user and 'anonymous' in user.username:
        if social:
            tmp_user = user
            logout(strategy.request)
            user = social.user
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(strategy.request, user)
            tmp_user.role_set.filter(role='self').update(role='student')
            union_merge(tmp_user, user)
            tmp_user.delete()
            return {'user': user}
        else:
            try:
                # TODO try to search django user email
                user.username = details.get('username')
                user.first_name = ''
                user.save()
                user.role_set.filter(role='self').update(role='student')
            except IntegrityError as e:
                _id = int(time.mktime(datetime.now().timetuple()))
                user.username = details.get('username') + str(_id)
                user.save()
    elif user and social and social.user != user:
        tmp_user = user
        logout(strategy.request)
        user = social.user
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(strategy.request, user)
        union_merge(tmp_user, user)
        social_merge(tmp_user, user)
        tmp_user.delete()
        return {'user': user}


def social_user(backend, uid, user=None, *args, **kwargs):
    provider = backend.name
    social = backend.strategy.storage.user.get_social_auth(provider, uid)
    if social:
        if not user or 'anonymous' in user.username:
            user = social.user
    return {'social': social,
            'user': user,
            'is_new': user is None,
            'new_association': False}


def associate_user(backend, details, uid, user=None, social=None, *args, **kwargs):
    email = details.get('email')
    if user and not social:
        try:
            social = backend.strategy.storage.user.create_social_auth(
                user, uid, backend.name
            )
        except Exception as err:
            if not backend.strategy.storage.is_integrity_error(err):
                raise
            # Protect for possible race condition, those bastard with FTL
            # clicking capabilities, check issue #131:
            #   https://github.com/omab/django-social-auth/issues/131
            return social_user(backend, uid, user, *args, **kwargs)
        else:
            if email and not user.email == email:
                secondary = SecondaryEmail(user=user,
                                           email=email,
                                           provider=social)
                secondary.save()
            return {'social': social,
                    'user': social.user,
                    'new_association': True}
