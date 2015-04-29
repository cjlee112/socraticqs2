from django.shortcuts import redirect
from django.shortcuts import render_to_response
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.conf import settings
from django.db import IntegrityError
from django.http import HttpResponseBadRequest

from psa.utils import render_to
from psa.models import AnonymEmail
from social.backends.utils import load_backends

from datetime import datetime


def context(**extra):
    return dict({
        'available_backends': load_backends(settings.AUTHENTICATION_BACKENDS),
    }, **extra)


@render_to('psa/custom_login.html')
def validation_sent(request):
    return context(
        validation_sent=True,
        email=request.session.get('email_validation_address')
    )


def custom_login(request):
    username = password = ''
    logout(request)
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('/ct/')
    return render_to_response('psa/custom_login.html',
                              context_instance=RequestContext(request,
                                                              {
                                                                  'available_backends': load_backends(
                                                                      settings.AUTHENTICATION_BACKENDS),
                                                              }))


@login_required
@render_to('ct/person.html')
def done(request):
    """Login complete view, displays user data"""
    return context(person=request.user)


@login_required
@render_to('ct/index.html')
def ask_stranger(request):
    return context(tmp_email_ask=True)


@login_required
@render_to('ct/person.html')
def set_pass(request):
    changed = False
    user = request.user
    if user.is_authenticated():
        if request.POST:
            password = request.POST['pass']
            confirm = request.POST['confirm']
            if password == confirm:
                user.set_password(password)
                user.save()
                changed = True
    if changed:
        return context(changed=True, person=user)
    else:
        return context(exception='Something goes wrong...', person=user)
