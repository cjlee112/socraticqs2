from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic.base import View

from ct.models import Course
from fsm.models import FSMState
from chat.models import EnrollUnitCode


class CourseView(View):

    @method_decorator(login_required)
    def get(self, request, course_id):
        """Show list of courselets in a course with proper context"""
        course = get_object_or_404(Course, pk=course_id)
        liveSession = FSMState.find_live_sessions(request.user).filter(
            activity__course=course
        ).first()
        courselets = (
            (courselet, EnrollUnitCode.get_code(courselet))
            for courselet in course.get_course_units(True)
        )
        return render(
            request, 'lms/course_page.html',
            dict(
                course=course,
                liveSession=liveSession,
                courslets=courselets
            )
        )
