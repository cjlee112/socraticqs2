import pickle
import oauth2
import json
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from ims_lti_py.tool_provider import DjangoToolProvider
from django.shortcuts import render_to_response, redirect

from lti.models import LTIUser
from lti import app_settings as settings


@csrf_exempt
def lti_init(request):
    if settings.LTI_DEBUG:
        print "META"
        print request.META
        print "PARAMS"
        print request.POST
    session = request.session
    session.clear()
    try:
        consumer_key = settings.CONSUMER_KEY
        secret = settings.LTI_SECRET

        tool = DjangoToolProvider(consumer_key, secret, request.POST)
        is_valid = tool.is_valid_request(request)
        session['message'] = "We are cool!"
    except oauth2.MissingSignature, e:
        is_valid = False
        session['message'] = "{}".format(e)
        pass
    except oauth2.Error, e:
        is_valid = False
        session['message'] = "{}".format(e)
        pass
    except KeyError, e:
        is_valid = False
        session['message'] = "{}".format(e)
        pass
    session['is_valid'] = is_valid
    # copy request to dictionary
    request_dict = dict()
    for r in request.POST.keys():
        request_dict[r] = request.POST[r]
    session['LTI_POST'] = pickle.dumps(request_dict)

    '-------------------------------------------------------------------------------'
    consumer_name = request_dict.get('ext_lms', 'lti')

    user_id = request_dict.get('user_id', None)
    course_id = request_dict.get('custom_course', None)
    roles = request_dict.get('roles', None)
    if not user_id or not course_id:
        return render_to_response("error.html",  RequestContext(request))
    course_id = int(course_id)

    user, created = LTIUser.objects.get_or_create(user_id=user_id,
                                                  consumer=consumer_name,
                                                  course_id=course_id)
    user.extra_data = json.dumps(request_dict) # TODO exclude not needed params
    user.save()

    if not user.is_linked:
        user.create_links()

    user.login(request)
    user.enroll(roles, course_id)
    '-------------------------------------------------------------------------------'

    if settings.LTI_DEBUG:
        print "session: is_valid = {}".format( session['is_valid'])
        print "session: message = {}".format( session['message'])
    if not is_valid:
        return render_to_response("error.html",  RequestContext(request))

    if user.is_enrolled(roles, course_id):
        # Redirect to course page
        return redirect(reverse('ct:course_student', args=(course_id,)))
    else:
        return redirect(reverse('ct:home'))
