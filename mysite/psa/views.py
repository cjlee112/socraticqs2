from django.shortcuts import redirect
from django.shortcuts import render_to_response
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.conf import settings

from .utils import render_to, clear_all_social_accounts
from social.backends.utils import load_backends


@render_to('psa/validation_sent.html')
def validation_sent(request):
    return {'email': request.session.get('email_validation_address')}


def custom_login(request):
    logout(request)
    username = password = ''
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
                                  'available_backends': load_backends(settings.AUTHENTICATION_BACKENDS),
                              }))