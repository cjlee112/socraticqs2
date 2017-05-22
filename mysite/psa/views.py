from django.contrib import messages
from django.db.models import Q
from django.conf import settings
from django.http.response import HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response, render
from django.contrib.auth import logout, login, authenticate, REDIRECT_FIELD_NAME
from django.core.urlresolvers import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from social.actions import do_complete
from social.apps.django_app.utils import psa
from social.backends.utils import load_backends
from social.apps.django_app.views import _do_login
from accounts.models import Instructor
from social.apps.django_app.views import complete as social_complete
from social.exceptions import AuthMissingParameter

from psa.utils import render_to
from psa.models import SecondaryEmail, AnonymEmail
from psa.forms import SignUpForm, EmailLoginForm, UsernameLoginForm, SocialForm


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


def custom_login(request, template_name='psa/custom_login.html', next_page='/ct/', login_form_cls=EmailLoginForm):
    """
    Custom login to integrate social auth and default login.
    """
    username = password = ''
    logout(request)
    if not next_page.startswith('/'):
        next_page = reverse(next_page)
    if request.method == 'GET' and 'next' in request.GET:
        next_page = request.GET['next']
    kwargs = dict(available_backends=load_backends(settings.AUTHENTICATION_BACKENDS))
    if request.POST:
        form = login_form_cls(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect(request.POST.get('next', next_page))
        messages.error(request, "We could not authenticate you, please correct errors below.")
    else:
        form = login_form_cls(initial={'next': next_page})
    kwargs['form'] = form
    kwargs['next'] = next_page
    return render(
        request,
        template_name,
        kwargs
    )


def check_username_and_create_user(username, email, password, **kwargs):
    already_exists = User.objects.filter(
        username=username
    )
    if not already_exists:
        return User.objects.create_user(
            username=username,
            password=password,
            first_name=kwargs['first_name'],
            last_name=kwargs['last_name'],

        )
    else:
        username += '_'
        return check_username_and_create_user(username, email, password, **kwargs)


@never_cache
@csrf_exempt
@psa('ctms:email_sent')
def custom_complete(request, backend, *args, **kwargs):
    """Authentication complete view"""
    request.session['resend_user_email'] = request.POST.get('email')
    return do_complete(request.backend, _do_login, request.user,
                       redirect_name=REDIRECT_FIELD_NAME, *args, **kwargs)


def signup(request, next_page=None):
    """
    This function handles custom login to integrate social auth and default login.
    """
    username = password = ''
    logout(request)

    next_page = request.POST.get('next') or request.GET.get('next') or next_page

    form = SignUpForm(initial={'next': next_page})
    kwargs = dict(available_backends=load_backends(settings.AUTHENTICATION_BACKENDS))
    if request.POST:
        form = SignUpForm(request.POST)
        # params = request.POST
        if form.is_valid():
            username = form.cleaned_data['email'].split('@', 2)[0]
            user = check_username_and_create_user(
                username=username,
                **form.cleaned_data
            )
            instructor = Instructor.objects.create(
                user=user,
                institution=form.cleaned_data['institution'],
            )
            # here we put just created user into request.user
            # because python-social-auth.compolete function implies that just created user will be authenticated,
            # but we don't authenticate it, so we do this trick.
            request.user = user
            response = custom_complete(request, 'email')
            # after calling complete function we don't need request.user, so we replace it with AnonymousUser
            request.user = AnonymousUser()
            return response
        else:
            messages.error(
                request, "We could not create the account. Please review the errors below."
            )
    # else:
        # params = request.GET
    # if 'next' in params:  # must pass through for both GET or POST
    #     kwargs['next'] = params['next']

    kwargs['form'] = form
    kwargs['next'] = next_page
    return render(request, 'psa/signup.html', kwargs)



def done(request):
    """
    Login complete view, displays user data.
    """
    @login_required
    @render_to('ct/person.html')
    def old_UI_wrap(request):
        return context(person=request.user)

    @login_required
    def new_UI_wrap(request):
        if not request.user.course_set.count():
            # if newly created user - show create_course page
            return HttpResponseRedirect(reverse('ctms:create_course'))
        return HttpResponseRedirect(reverse('ctms:my_courses'))

    # NOTE: IF USER has attached instructor instance will be redirected to /ctms/ (ctms dashboard)
    if getattr(request.user, 'instructor', None):
        return new_UI_wrap(request)

    return old_UI_wrap(request)


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
