from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.conf import settings

from social.pipeline.partial import partial
from social.exceptions import InvalidEmail, AuthAlreadyAssociated
from ct.models import Role



@partial
def password_check(strategy, user, *args, **kwargs):
    if not user.has_usable_password() and user.social_auth.count() == 1:
        if strategy.request.POST.get('password'):
            user.set_password(strategy.request.POST['password'])
            user.save()
        else:
            return render_to_response('require_password.html', {
                'request': strategy.request,
                'next': strategy.request.POST.get('next') or ''
            }, RequestContext(strategy.request))


@partial
def password_ask(strategy, details, user=None, is_new=False, *args, **kwargs):
    print('password_ask')
    print(details)
    print(kwargs)
    if is_new or 'anonymous' in user.username:
        email = user.email or details.get('email')
        if strategy.request.POST.get('password'):
            if 'anonymous' in user.username:
                user.username = details.get('username')
                user.first_name = ''
            username = user.username
            password = strategy.request.POST.get('password')
            user.set_password(password)
            user.save()
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
    print('custom_email_validation')
    print(kwargs)
    print(details)
    requires_validation = backend.REQUIRES_EMAIL_VALIDATION or \
                          backend.setting('FORCE_EMAIL_VALIDATION', False)
    send_validation = details.get('email') and \
                      (is_new or backend.setting('PASSWORDLESS', False))

    if requires_validation and send_validation and backend.name == 'email':
        data = backend.strategy.request_data()
        if 'verification_code' in data:
            print(kwargs)
            backend.strategy.session_pop('email_validation_address')
            if not backend.strategy.validate_email(details['email'],
                                           data['verification_code']):
                raise InvalidEmail(backend)
        else:
            backend.strategy.send_email_validation(backend, details['email'])
            backend.strategy.session_set('email_validation_address',
                                         details['email'])
            return backend.strategy.redirect(
                backend.strategy.setting('EMAIL_VALIDATION_URL')
            )


def associate_by_email(backend, details, user=None, *args, **kwargs):
    """
    Associate current auth with a user with the same email address in the DB.

    This pipeline entry is not 100% secure unless you know that the providers
    enabled enforce email verification on their side, otherwise a user can
    attempt to take over another user account by using the same (not validated)
    email address on some provider.  This pipeline entry is disabled by
    default.
    """
    print('associate_by_email')
    print(user)
    print(kwargs)
    print(kwargs.get('anonym'))
    if user:
        return None

    email = details.get('email')
    if email:
        # Try to associate accounts registered with the same email address,
        # only if it's a single object. AuthException is raised if multiple
        # objects are returned.
        users = list(backend.strategy.storage.user.get_users_by_email(email))
        if len(users) == 0:
            return None
        elif len(users) > 1:
            raise AuthException(
                backend,
                'The given email address is associated with another account'
            )
        else:
            return {'user': users[0]}


def social_user(backend, uid, user=None, *args, **kwargs):
    print('social_user')
    print(user)

    print(kwargs)
    provider = backend.name
    social = backend.strategy.storage.user.get_social_auth(provider, uid)
    if social:
        if user and not 'anonymous' in user.username and social.user != user:
            print(1)
            msg = 'This {0} account is already in use.'.format(provider)
            raise AuthAlreadyAssociated(backend, msg)
        elif not user or 'anonymous' in user.username:
            print(2)
            user = social.user

    return {'social': social,
            'user': user,
            'is_new': user is None,
            'new_association': False}


def role_set(strategy, details, user=None, *args, **kwargs):
    print('role_set')
    print('user', user)
    if 'anonymous' in user.username:
        print('anonym_role_set')
        # user.role_set.all().update(user=user)


def create_user(strategy, details, user=None, *args, **kwargs):
    print(details)
    if user:
        username = user.username
    if user or 'anonymous' in username:
        return {'is_new': False}

    fields = dict((name, kwargs.get(name) or details.get(name))
                        for name in strategy.setting('USER_FIELDS',
                                                      USER_FIELDS))
    if not fields:
        return

    return {
        'is_new': True,
        'user': strategy.create_user(**fields)
    }