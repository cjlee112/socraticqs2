from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.conf import settings
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response
from django.contrib.auth import logout, login, authenticate

from social.backends.utils import load_backends
from social.apps.django_app.views import complete as social_complete
from social.exceptions import AuthMissingParameter
from psa.forms import CompleteEmailForm

from psa.utils import render_to
from psa.models import SecondaryEmail


def context(**extra):
    """
    Adding default context to rendered page.
    """
    return dict({
        'available_backends': load_backends(settings.AUTHENTICATION_BACKENDS),
    }, **extra)


@render_to('psa/custom_login.html')
def validation_sent(request):
    """
    View to handle validation_send action.
    """
    user = request.user
    social_list = []
    email = request.session.get('email_validation_address')
    if user and user.is_anonymous():
        by_secondary = [i.provider.provider for i in
                        SecondaryEmail.objects.filter(email=email)
                        if not i.provider.provider == u'email']
        social_list.extend(by_secondary)

        users_by_email = User.objects.filter(email=email)
        for user_by_email in users_by_email:
            by_primary = [i.provider for i in
                          user_by_email.social_auth.all()
                          if not i.provider == u'email' and
                          not SecondaryEmail.objects.filter(
                              ~Q(email=email), provider=i, user=user_by_email
                          ).exists()]
            social_list.extend(by_primary)

    return context(
        validation_sent=True,
        email=email,
        social_propose=bool(social_list),
        social_list=social_list
    )


def custom_login(request):
    """
    Custom login to integrate social auth and default login.
    """
    username = password = ''
    logout(request)
    kwargs = dict(available_backends=load_backends(settings.AUTHENTICATION_BACKENDS))
    if request.POST:
        params = request.POST
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect(request.POST.get('next', '/ct/'))
    else:
        params = request.GET
    if 'next' in params:  # must pass through for both GET or POST
        kwargs['next'] = params['next']
    return render_to_response(
        'psa/custom_login.html', context_instance=RequestContext(request, kwargs)
    )


@login_required
@render_to('ct/person.html')
def done(request):
    """
    Login complete view, displays user data.
    """
    return context(person=request.user)


@login_required
@render_to('ct/index.html')
def ask_stranger(request):
    """
    View to handle stranger whend asking email.
    """
    return context(tmp_email_ask=True)


@login_required
@render_to('ct/person.html')
def set_pass(request):
    """
    View to handle password set / change action.
    """
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


def complete(request, *args, **kwargs):
    form = CompleteEmailForm(request.POST or request.GET)
    if form.is_valid():
        try:
            return social_complete(request, 'email', *args, **kwargs)
        except AuthMissingParameter:
            messages.error(
                request,
                "Email already verified. Please log in using form below or sign up."
            )
            if request.user.is_authenticated():
                return redirect('ct:person_profile', user_id=request.user.id)
            return redirect('ct:home')
    else:
        # add message with transformed form errors
        err_msg = "\n".join([
            "{} - {}".format(
                k.capitalize(), ", ".join(i.lower() for i in v)
            )
            for k, v in form.errors.items()
        ])
        messages.error(
            request,
            "You passed not correct data. {}".format(err_msg)
        )
        # if form is not valid redirect user to page where he came from
        return redirect(reverse("login"))

