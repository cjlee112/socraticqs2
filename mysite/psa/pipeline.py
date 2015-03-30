from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.mail import send_mail
from django.conf import settings


from social.pipeline.partial import partial


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


from social.exceptions import InvalidEmail
from social.pipeline.partial import partial


@partial
def custom_mail_validation(backend, details, is_new=False, *args, **kwargs):
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
            backend.strategy.send_email_validation(backend, details['email'])
            backend.strategy.session_set('email_validation_address',
                                         details['email'])
            return backend.strategy.redirect(
                backend.strategy.setting('EMAIL_VALIDATION_URL')
            )
