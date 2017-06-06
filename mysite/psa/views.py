from django.contrib import messages
from django.contrib.auth.hashers import make_password
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
from psa.custom_django_storage import CustomCode

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
    u_hash_sess = request.session.get('u_hash')
    logout(request)
    if u_hash_sess:
        request.session['u_hash'] = u_hash_sess

    if not next_page.startswith('/'):
        next_page = reverse(next_page)
    if request.method == 'GET' and 'next' in request.GET:
        next_page = request.GET['next']
    kwargs = dict(available_backends=load_backends(settings.AUTHENTICATION_BACKENDS))
    form_initial = {'next': next_page, 'u_hash': request.POST.get('u_hash')}
    if request.POST:
        form = login_form_cls(request.POST, initial=form_initial)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if request.POST.get('u_hash') and request.POST['u_hash'] == u_hash_sess:
                        del request.session['u_hash']
                        return redirect('ctms:shared_courses')
                    return redirect(request.POST.get('next', next_page))
        messages.error(request, "We could not authenticate you, please correct errors below.")
    else:
        form = login_form_cls(initial=form_initial)
    kwargs['form'] = form
    kwargs['next'] = next_page
    return render(
        request,
        template_name,
        kwargs
    )


@never_cache
@csrf_exempt
@psa('ctms:email_sent')
def custom_complete(request, backend, u_hash, u_hash_sess, *args, **kwargs):
    """Authentication complete view"""
    if u_hash and u_hash == u_hash_sess:
        # if invited tester join course - create user immediately without confirmation email.
        data = request.POST.dict().copy()
        pw = make_password(request.POST.get('password'))
        data['password'] = pw
        user = request.backend.strategy.create_user(**data)
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        request.session['u_hash'] = u_hash

    response = do_complete(
        request.backend, _do_login, request.user,
        redirect_name=REDIRECT_FIELD_NAME, *args, **kwargs)

    if not u_hash or u_hash != u_hash_sess:
        # if not invited tester join course - logout user
        logout(request)

        # add resend_user_email to the session to be able to resend link
        request.session['resend_user_email'] = request.POST.get('email')
        # getting just created CustomCode
        cc = CustomCode.objects.filter(email=request.POST.get('email')).order_by('-id').first()
        if cc:
            request.session['cc_id'] = cc.id
    # remove u_hash from session
    request.session.pop('u_hash', None)
    return response


def signup(request, next_page=None):
    """
    This function handles custom login to integrate social auth and default login.
    """
    username = password = ''
    u_hash = request.POST.get('u_hash')
    u_hash_sess = request.session.get('u_hash')

    logout(request)
    if u_hash and u_hash == u_hash_sess:
        # if we have u_hash and it's equal with u_hash from session
        # replace next url with shared_courses page url
        next_page = reverse('ctms:shared_courses')
        request.session['next'] = next_page
        post = request.POST.copy()
        post['next'] = next_page
        request.POST = post
    else:
        next_page = request.POST.get('next') or request.GET.get('next') or next_page

    form = SignUpForm(initial={'next': next_page, 'u_hash': u_hash})
    kwargs = dict(available_backends=load_backends(settings.AUTHENTICATION_BACKENDS))
    if request.POST:
        form = SignUpForm(request.POST)
        # params = request.POST
        if form.is_valid():
            response = custom_complete(request, 'email', u_hash=u_hash, u_hash_sess=u_hash_sess)
            return response
        else:
            messages.error(
                request, "We could not create the account. Please review the errors below."
            )
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
