from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

# Create your views here.
from ct.forms import NewUnitTitleForm, ReorderForm, set_crispy_action
from ct.models import Course
from ct.templatetags.ct_extras import is_teacher_url, md2html
from ct.views import PageData, course_tabs, check_instructor_auth
from fsm.models import FSMState


@login_required
def course_view(request, course_id):
    'show courselets in a course'
    course = get_object_or_404(Course, pk=course_id)
    liveSession = FSMState.find_live_sessions(request.user).filter(activity__course=course).first()
    return render(
        request, 'lms/course_page.html',
        dict(course=course, liveSession=liveSession, courslets=course.get_course_units(True))
    )