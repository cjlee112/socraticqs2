from django.shortcuts import redirect
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required

from .utils import render_to, clear_all_social_accounts


@render_to('psa/validation_sent.html')
def validation_sent(request):
    return {'email': request.session.get('email_validation_address')}


@login_required
def primary_email(request, usa_id):
    usa_id = int(usa_id)
    for usa in request.user.social_auth.filter(provider='email'):
        usa.set_extra_data({'primary': usa.id == usa_id})
        usa.save()
    return redirect('demo_feature_6')
