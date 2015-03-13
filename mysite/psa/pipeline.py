from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth import login, logout
# from django.core.mail import send_mail
from django.conf import settings
from django.db import IntegrityError
import time
from datetime import datetime

from social.pipeline.partial import partial
from social.exceptions import InvalidEmail, AuthException, AuthAlreadyAssociated
from social.backends.utils import load_backends
from social.apps.django_app.default.models import UserSocialAuth

from psa.models import AnonymEmail, SecondaryEmail


# @partial
# def password_ask(strategy, details, user=None, is_new=False, *args, **kwargs):
# if is_new and kwargs.get('backend').name == 'email':
#         email = user.email or details.get('email')
#         if strategy.request.POST.get('password'):
#             if 'anonymous' in user.username:
#                 user.username = details.get('username')
#                 user.first_name = ''
#             username = user.username
#             password = strategy.request.POST.get('password')
#             user.set_password(password)
#             user.save()
#             if email:
#                 send_mail('Account is created',
#                           'Account is created.\nUsername: {0}\nPassword: {1}'.format(username,
#                                                                                      password),
#                           settings.EMAIL_FROM,
#                           [email],
#                           fail_silently=False)
#         else:
#             return render_to_response('psa/require_password.html', {
#                 'request': strategy.request,
#                 'next': strategy.request.POST.get('next') or ''
#             }, RequestContext(strategy.request))


@partial
def custom_mail_validation(backend, details, user=None, is_new=False, *args, **kwargs):
    requires_validation = backend.REQUIRES_EMAIL_VALIDATION or \
                          backend.setting('FORCE_EMAIL_VALIDATION', False)
    send_validation = (details.get('email') and
                       (is_new or backend.setting('PASSWORDLESS', False)))

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


@partial
def validated_user_details(strategy, backend, details, user=None, is_new=False, *args, **kwargs):
    """Merge actions

    Make different merge actions based on user type.
    """
    social = kwargs.get('social')
    email = details.get('email')
    if user and 'anonymous' in user.username:
        if social:
            tmp_user = user
            logout(strategy.request)
            user = social.user
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(strategy.request, user)
            union_merge(tmp_user, user)
            tmp_user.delete()
            return {'user': user}
        else:
            try:
                new = False
                if email:
                    users = list(backend.strategy.storage.user.get_users_by_email(email))
                    if len(users) == 0:
                        pass
                    elif len(users) > 1:
                        raise AuthException(
                            backend,
                            'The given email address is associated with another account'
                        )
                    else:
                        new = users[0]
                if not new:
                    user.username = details.get('username')
                    user.first_name = ''
                    user.save()
                else:
                    tmp_user = user
                    logout(strategy.request)
                    user = new
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(strategy.request, user)
                    union_merge(tmp_user, user)
                    tmp_user.delete()
                    return {'user': user}
            except IntegrityError as e:
                _id = int(time.mktime(datetime.now().timetuple()))
                user.username = details.get('username') + str(_id)
                user.save()
    elif user and social and social.user != user:
        confirm = strategy.request.POST.get('confirm')
        if confirm and confirm == 'no':
            raise AuthException(
                backend,
                'You interrupted merge process.'
            )
        elif (not user.get_full_name() == social.user.get_full_name() and
                  not strategy.request.POST.get('confirm') and
                  not user.email == social.user.email):
            return render_to_response('ct/person.html', {
                'available_backends': load_backends(settings.AUTHENTICATION_BACKENDS),
                'request': strategy.request,
                'next': strategy.request.POST.get('next') or '',
                'target_name': social.user.get_full_name(),
                'own_name': user.get_full_name(),
                'person': user,
                'merge_confirm': True
            }, RequestContext(strategy.request))
        elif (user.get_full_name() == social.user.get_full_name()
              or confirm and confirm == 'yes'
              or user.email == social.user.email):
            union_merge(social.user, user)
            social_merge(social.user, user)
            social.user.delete()
            social.user = user
            return {'user': user,
                    'social': social}


def not_allowed_to_merge(user, social_user):
    user_auths = set([i.provider for i in user.social_auth.all()])
    social_user_auths = set([i.provider for i in social_user.social_auth.all()])

    return user_auths.intersection(social_user_auths)


def social_user(backend, uid, user=None, *args, **kwargs):
    provider = backend.name
    social = backend.strategy.storage.user.get_social_auth(provider, uid)
    if social:
        if user and social.user != user and 'anonymous' not in user.username:
            if not_allowed_to_merge(user, social.user):
                msg = 'Merge aborted due to providers intersection.'
                raise AuthAlreadyAssociated(backend, msg)
        elif not user or 'anonymous' in user.username:
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
            # https://github.com/omab/django-social-auth/issues/131
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


def associate_by_email(backend, details, user=None, *args, **kwargs):
    """
    Associate current auth with a user with the same email address in the DB.

    This pipeline entry is not 100% secure unless you know that the providers
    enabled enforce email verification on their side, otherwise a user can
    attempt to take over another user account by using the same (not validated)
    email address on some provider.  This pipeline entry is disabled by
    default.
    """
    if user:
        return None

    email = details.get('email')
    if email:
        # Try to associate accounts registered with the same email address,
        # only if it's a single object. AuthException is raised if multiple
        # objects are returned.
        users = list(backend.strategy.storage.user.get_users_by_email(email))
        if len(users) == 0:
            socials = UserSocialAuth.objects.filter(uid=email,
                                                    provider=u'email')
            if socials:
                return {'user': socials[0].user}
            else:
                return None
        elif len(users) > 1:
            raise AuthException(
                backend,
                'The given email address is associated with another account'
            )
        else:
            return {'user': users[0]}
