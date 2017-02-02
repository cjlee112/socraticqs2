from django.db.models import Q
from django.conf import settings
from django.template import RequestContext
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render_to_response, render
from django.contrib.auth import logout, login, authenticate
from social.backends.utils import load_backends
from social.apps.django_app.views import complete
from accounts.models import Instructor

from psa.utils import render_to
from psa.models import SecondaryEmail, AnonymEmail
from psa.forms import SignUpForm


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


def custom_login(request, template_name='psa/custom_login.html', next_page='/ct/'):
    """
    Custom login to integrate social auth and default login.
    """
    username = password = ''
    logout(request)
    kwargs = dict(available_backends=load_backends(settings.AUTHENTICATION_BACKENDS))
    if request.POST:
        params = request.POST
        username = request.POST.get('username')
        password = request.POST['password']
        email = request.POST.get('email')

        if not username and email:
            user = User.objects.filter(email=email).first()
            if not user:
                sec_mail = SecondaryEmail.objects.filter(
                    email=email
                ).first()
                if sec_mail:
                    user = sec_mail.user
            if user:
                username = user.username

        # remove empty value
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect(request.POST.get('next', next_page))
    else:
        params = request.GET
    if 'next' in params:  # must pass through for both GET or POST
        kwargs['next'] = params['next']
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

def send_confirmation_email(user):
    '''
    This function will send email about successful registration to user.
    :param user: user instance
    :return: None
    '''
    return True

def signup(request, next_page=None):
    """
    Fields to handle on:
        Email
        Re-enter email
        First name
        Last name
        Institution
        Password
    Custom login to integrate social auth and default login.
    """
    username = password = ''
    logout(request)
    form = SignUpForm(initial={'next': next_page})
    kwargs = dict(available_backends=load_backends(settings.AUTHENTICATION_BACKENDS))
    if request.POST:
        form = SignUpForm(request.POST)
        params = request.POST
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
            # params = form.cleaned_data
            # username = user.username
            # password = params['password']

            request.user = user
            response = complete(request, 'email')
            request.user = AnonymousUser()
            return response
            # user = authenticate(username=username, password=password)
            # if user is not None:
            #     email_sent = send_confirmation_email(user)
            #     if user.is_active:
            #         login(request, user)
            #         return redirect(request.POST.get('next', next_page))
    else:
        params = request.GET
    if 'next' in params:  # must pass through for both GET or POST
        kwargs['next'] = params['next']
    kwargs['form'] = form
    return render(request, 'psa/signup.html', kwargs)


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
