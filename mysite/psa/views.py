from django.shortcuts import redirect
from django.shortcuts import render_to_response
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.conf import settings
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest, Http404

from .utils import render_to, clear_all_social_accounts
from social.backends.utils import load_backends
from psa.models import AnonymEmail

from datetime import datetime


@render_to('psa/validation_sent.html')
def validation_sent(request):
    return {'email': request.session.get('email_validation_address')}


def custom_login(request):
    username = password = ''
    if request.POST:
        logout(request)
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
                                  'available_backends': load_backends(settings.AUTHENTICATION_BACKENDS),
                              }))



# TODO Rewrite to user django-rest APIView
@login_required
def change_anonym_email(request):
    if request.POST:
        email = request.POST.get('email').lower()
        user = request.user
        try:
            email = AnonymEmail(user=user, email=email, date=datetime.now())
            email.save()
        except IntegrityError:
            return HttpResponseBadRequest('Improperly configured request.')
        return redirect('/ct/')
    else:
        return render_to_response('psa/anonym-email-change.html',
                              context_instance=RequestContext(request))


def anonym_restore(request):
    return render_to_response('psa/anonym-restore.html',
                               context_instance=RequestContext(request))