import re

from django import template
from django.conf import settings
from collections import defaultdict

from social.backends.utils import load_backends
from social.backends.oauth import OAuthAuth

from psa.models import SecondaryEmail


register = template.Library()
name_re = re.compile(r'([^O])Auth')


@register.filter
def backend_name(backend):
    name = backend.__class__.__name__
    name = name.replace('OAuth2', '')
    name = name.replace('OAuth1', '')
    name = name.replace('OAuth', '')
    name = name.replace('Auth', '')
    name = name.replace('OpenId', '')
    name = name.replace('Sandbox', '')
    name = name_re.sub(r'\1 Auth', name)
    return name


@register.filter
def backend_class(backend):
    return backend.name.replace('-', ' ')


@register.filter
def presentation_name(name):
    return {
        'stackoverflow': 'Stack-overflow',
        'google-oauth': 'Google',
        'google-oauth2': 'Google',
        'google-openidconnect': 'Google',
        'yahoo-oauth': 'Yahoo',
        'facebook-app': 'Facebook',
        'email': 'Email',
        'vimeo': 'Vimeo-square',
        'linkedin-oauth2': 'Linkedin',
        'vk-oauth2': 'Vk',
        'live': 'Windows',
        'username': 'User',
    }.get(name, name)


@register.filter
def icon_name(name):
    return {
        'stackoverflow': 'stack-overflow',
        'google-oauth': 'google',
        'google-oauth2': 'google',
        'google-openidconnect': 'google',
        'yahoo-oauth': 'yahoo',
        'facebook-app': 'facebook',
        'email': 'envelope',
        'vimeo': 'vimeo-square',
        'linkedin-oauth2': 'linkedin',
        'vk-oauth2': 'vk',
        'live': 'windows',
        'username': 'user',
    }.get(name, name)


@register.filter
def social_backends(backends):
    backends = [(name, backend) for name, backend in backends.items()
                if name not in ['username', 'email']]
    backends.sort(key=lambda b: b[0])

    return [backends[n:n + 10] for n in range(0, len(backends), 10)]


@register.filter
def legacy_backends(backends):
    backends = [(name, backend) for name, backend in backends.items()
                if name in ['username', 'email']]
    backends.sort(key=lambda b: b[0])

    return [backends[n:n + 10] for n in range(0, len(backends), 10)]


# @register.filter
# def all_backends(backends):
#     backends = [(name, backend) for name, backend in backends.items()]
#     backends.sort(key=lambda b: b[0])
#
#     return [backends[n:n + 10] for n in range(0, len(backends), 10)]


# @register.filter
# def oauth_backends(backends):
#     backends = [(name, backend) for name, backend in backends.items()
#                 if issubclass(backend, OAuthAuth)]
#     backends.sort(key=lambda b: b[0])
#     return backends


@register.simple_tag(takes_context=True)
def associated(context, backend):
    user = context.get('user')
    context['association'] = None
    if user and user.is_authenticated():
        try:
            context['association'] = user.social_auth.filter(
                provider=backend.name
            )[0]
        except IndexError:
            pass
    return ''


# @register.simple_tag(takes_context=True)
# def anonym_email(context):
#     email = context['user'].anonymemail_set.all()
#     if email:
#         context['a_email'] = email[0].email
#     return ''


@register.simple_tag(takes_context=True)
def similar_backends(context):
    backends = load_backends(settings.AUTHENTICATION_BACKENDS)
    user = context.get('user')

    secondary_users = SecondaryEmail.objects.filter(email=user.email).exclude(user=user)
    similar_users = defaultdict(list)

    for secondary in secondary_users:
        similar_users[secondary.user].append((secondary.provider.provider,
                                              backends.get(secondary.provider.provider)))

    similar_users = dict(similar_users)
    context['similar_users'] = similar_users
    return ''
