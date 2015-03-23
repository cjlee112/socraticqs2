from social.apps.django_app.middleware import SocialAuthExceptionMiddleware
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from social import exceptions as social_exceptions  
from django.contrib import messages   


class MySocialAuthExceptionMiddleware(SocialAuthExceptionMiddleware):
    """
    Handler for Social exceptions such as AuthAlreadyAssociated
    """
    def process_exception(self, request, exception):
        if hasattr(social_exceptions, exception.__class__.__name__):
            user_id = request.user.id
            except_msg = "Attention: %s" % exception
            messages.add_message(request, messages.INFO, except_msg)
            return HttpResponseRedirect(reverse('ct:person_profile',
                                                kwargs={'user_id': user_id}))
        else:
            raise exception
