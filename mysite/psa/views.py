from django.shortcuts import redirect
from django.shortcuts import render_to_response
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.conf import settings
from django.contrib.auth.models import User

from psa.utils import render_to
from psa.models import SecondaryEmail
from social.backends.utils import load_backends


def context(**extra):
    return dict({
        'available_backends': load_backends(settings.AUTHENTICATION_BACKENDS),
    }, **extra)


@render_to('psa/custom_login.html')
def validation_sent(request):
    user = request.user
    social_propose = False
    by_secondary = []
    email = request.session.get('email_validation_address')
    if user and user.is_anonymous():
        by_secondary = [i.provider.provider for i in
                        SecondaryEmail.objects.filter(email=email)
                        if not i.provider.provider == u'email']
        if by_secondary:
            social_propose = True

        user_by_email = User.objects.filter(email=email)

        if len(user_by_email) == 1:
            by_primary = [i.provider for i in
                          user_by_email[0].social_auth.all()
                          if not i.provider == u'email']
            by_secondary.extend(by_primary)
            social_propose = True

    return context(
        validation_sent=True,
        email=email,
        social_propose=social_propose,
        social_list=by_secondary
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
