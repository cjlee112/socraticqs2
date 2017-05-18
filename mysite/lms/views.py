from django.contrib.staticfiles.templatetags.staticfiles import static
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from django.db import models

from ct.models import Course
from ctms.models import Invite
from fsm.models import FSMState
from chat.models import EnrollUnitCode, Chat, Message
from chat.serializers import ChatProgressSerializer
from mysite.mixins import NewLoginRequiredMixin


class CourseView(View):
    template_name = 'lms/course_page.html'

    def get_courselets(self, request, course):
        return [
            {
                'courselet': courselet,
                'enroll_code': EnrollUnitCode.get_code(courselet),
                'execrices': len(courselet.unit.get_exercises()),
                'chat': Chat.objects.filter(
                    enroll_code__courseUnit=courselet
                ).first()
            }
            for courselet in course.get_course_units(True)
        ]

    @method_decorator(login_required)
    def get(self, request, course_id):
        """Show list of courselets in a course with proper context"""
        course = get_object_or_404(Course, pk=course_id)
        liveSession = FSMState.find_live_sessions(request.user).filter(
            activity__course=course
        ).first()
        if liveSession:
            liveSession.live_instructor_name = (
                liveSession.user.get_full_name() or liveSession.user.username
            )
            try:
                liveSession.live_instructor_icon = (
                    liveSession.user.instructor.icon_url or static('img/avatar-teacher.jpg')
                )
            except AttributeError:
                liveSession.live_instructor_icon = static('img/avatar-teacher.jpg')
        courselets = self.get_courselets(request, course)
        live_sessions_history = Chat.objects.filter(
            user=request.user,
            is_live=True,
            enroll_code__courseUnit__course=course,
            state__isnull=True
        )
        # TODO: once django updated to version >=1.8 change next lines to
        # TODO: .annotate(lessons_count=models.Case()).
        # TODO: http://stackoverflow.com/questions/30752268/how-to-filter-objects-for-count-annotation-in-django

        for chat in live_sessions_history:
            chat.lessons_done = Message.objects.filter(
                chat=chat,
                contenttype='unitlesson',
                kind='orct',
                type='message',
                owner=request.user,
            ).count()
            if not chat.lessons_done:
                chat.delete()

        courslet_history = Chat.objects.filter(
            user=request.user,
            is_live=False,
            enroll_code__courseUnit__course=course,
            state__isnull=True
        )

        return render(
            request,
            self.template_name,
            dict(
                course=course,
                liveSession=liveSession,
                courslets=courselets,
                courslet_history=courslet_history,
                livesessions=live_sessions_history,
            )
        )

class TesterCourseView(NewLoginRequiredMixin, CourseView):

    template_name = 'lms/tester_course_page.html'

    def get_courselets(self, request, course):
        Invite.get_by_user_or_404(user=self.request.user, course=course, status='joined', type='tester')
        return (
            (
                courselet,
                EnrollUnitCode.get_code(courselet, isTest=True),
                len(courselet.unit.get_exercises())
            )
            for courselet in course.get_course_units(False)
        )

