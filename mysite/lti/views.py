import oauth2
import json
import logging
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from ims_lti_py.tool_provider import DjangoToolProvider
from django.shortcuts import render_to_response, redirect

from lti.utils import only_lti
from lti import app_settings as settings
from lti.models import LTIUser, CourseRef
from ct.models import Course, Role


ROLES_MAP = {
    'Instructor': Role.INSTRUCTOR,
    'Learner': Role.ENROLLED,
}

MOODLE_PARAMS = (
    'user_id',
    'context_id',
    'lis_person_name_full',
    'lis_person_name_given',
    'lis_person_name_family',
    'lis_person_sourcedid',
    'tool_consumer_instance_guid',
    'lis_person_contact_email_primary',
    'tool_consumer_info_product_family_code',
)

LOGGER = logging.getLogger('lti_debug')


@csrf_exempt
def lti_init(request, course_id=None, unit_id=None):
    """LTI init view

    Analyze LTI POST request to start LTI session.

    :param course_id: course id from launch url
    :param unit_id: unit id from lunch url
    """
    if settings.LTI_DEBUG:
        LOGGER.info(request.META)
        LOGGER.info(request.POST)
    session = request.session
    # Code from ims_lti_py_django example
    session.clear()
    try:
        consumer_key = settings.CONSUMER_KEY
        secret = settings.LTI_SECRET

        tool = DjangoToolProvider(consumer_key, secret, request.POST)
        is_valid = tool.is_valid_request(request)
        session['target'] = '_blank'
    except (oauth2.MissingSignature,
            oauth2.Error,
            KeyError,
            AttributeError) as err:
        is_valid = False
        session['message'] = "{}".format(err)

    session['is_valid'] = is_valid
    session['LTI_POST'] = {k: v for (k, v) in request.POST.iteritems()}

    if settings.LTI_DEBUG:
        msg = 'session: is_valid = {}'.format(session.get('is_valid'))
        LOGGER.info(msg)
        if session.get('message'):
            msg = 'session: message = {}'.format(session.get('message'))
            LOGGER.info(msg)
    if not is_valid:
        return render_to_response(
            'lti/error.html',
            {'message': 'LTI request is not valid'},
            RequestContext(request)
        )

    return lti_redirect(request, course_id, unit_id)


def lti_redirect(request, course_id=None, unit_id=None):
    """Create user and redirect to Course

    |  Create LTIUser with all needed link to Django user
    |  and/or UserSocialAuth.
    |  Finally login Django user and redirect to Course

    :param unit_id: unit id from lunch url
    """
    request_dict = request.session['LTI_POST']

    context_id = request_dict.get('context_id')
    course_ref = CourseRef.objects.filter(context_id=context_id).first()
    consumer_name = request_dict.get('tool_consumer_info_product_family_code', 'lti')
    user_id = request_dict.get('user_id', None)
    roles_from_request = request_dict.get('roles', '').split(',')
    roles = list(set((ROLES_MAP.get(role, Role.ENROLLED) for role in roles_from_request)))

    if not user_id:
        return render_to_response(
            'lti/error.html',
            {'message': 'There is not user_id required LTI param'},
            RequestContext(request)
        )

    user, created = LTIUser.objects.get_or_create(
        user_id=user_id,
        consumer=consumer_name,
        context_id=request_dict.get('context_id')
    )
    extra_data = {k: v for (k, v) in request_dict.iteritems()
                  if k in MOODLE_PARAMS}
    user.extra_data = json.dumps(extra_data)
    user.save()

    if not user.is_linked:
        user.create_links()
    user.login(request)

    if not course_id or not Course.objects.filter(id=course_id).exists():
        if course_ref:
            course_id = course_ref.course.id
        elif Role.INSTRUCTOR in roles:
            return redirect(reverse('lti:create_courseref'))
        else:
            return render_to_response(
                'lti/error.html',
                {'message': """You are trying to access Course that does not exists but
                            Students can not create new Courses automatically"""},
                RequestContext(request)
            )

    user.enroll(roles, course_id)

    if user.is_enrolled(roles, course_id):
        # Redirect to course or unit page considering users role
        if not unit_id:
            dispatch = 'ct:course_student'
            if Role.INSTRUCTOR in roles:
                dispatch = 'ct:course'
            return redirect(reverse(dispatch, args=(course_id,)))
        else:
            dispatch = 'ct:study_unit'
            if Role.INSTRUCTOR in roles:
                dispatch = 'ct:unit_tasks'
            return redirect(reverse(dispatch, args=(course_id, unit_id)))
    else:
        return redirect(reverse('ct:home'))


@only_lti
def create_courseref(request):
    """
    Create CourseRef and Course entry based on context_title.
    """
    request_dict = request.session['LTI_POST']
    if not request.session.get('is_valid'):
        return redirect(reverse('ct:home'))
    context_id = request_dict.get('context_id')
    roles_from_request = request_dict.get('roles', '').split(',')
    roles = list(set((ROLES_MAP.get(role, Role.ENROLLED) for role in roles_from_request)))
    # Make sure this context_id is not used
    course_ref = CourseRef.objects.filter(context_id=context_id).first()
    if course_ref:
        if Role.INSTRUCTOR in roles:
            return redirect(reverse('ct:course', args=(course_ref.course.id,)))
        else:
            return redirect(reverse('ct:home'))

    course = Course(
        title=request_dict.get('context_title', 'Course title for %s' % context_id),
        addedBy=request.user
    )
    course.save()
    role = Role(role=Role.INSTRUCTOR, course=course, user=request.user)
    role.save()
    course_id = course.id
    course_ref = CourseRef(
        course=course,
        context_id=context_id,
        tc_guid=request_dict.get('tool_consumer_instance_guid', request.META.get('HTTP_HOST'))
    )
    course_ref.save()
    course_ref.instructors.add(request.user)

    return redirect(reverse('ct:edit_course', args=(course_id,)))
