import smtplib

from social.apps.django_app.middleware import SocialAuthExceptionMiddleware
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from social import exceptions as social_exceptions
from django.contrib import messages
from django.template import RequestContext

from mysite.log import write_exception_to_log


class MySocialAuthExceptionMiddleware(SocialAuthExceptionMiddleware):
    """Handler for Social exceptions such as AuthAlreadyAssociated"""
    def process_exception(self, request, exception):
        if hasattr(social_exceptions, exception.__class__.__name__):
            user_id = request.user.id
            messages.add_message(request, messages.INFO, exception)
            if user_id:
                return HttpResponseRedirect(reverse('ct:person_profile',
                                                    kwargs={'user_id': user_id}))
            else:
                return HttpResponseRedirect(reverse('ct:home'))
        elif hasattr(smtplib, exception.__class__.__name__):
            write_exception_to_log(exception)
            return render_to_response(
                    'ct/error.html',
                    {'message': 'Something goes wrong with email sending. Please try again later.'},
                    RequestContext(request)
                                    )
        else:
            raise exception

