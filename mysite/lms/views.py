from django.contrib.staticfiles.templatetags.staticfiles import static
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic.base import View

from chat.models import EnrollUnitCode, Chat, Message
from ct.models import Course
from ctms.models import Invite
from fsm.models import FSMState
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
                    enroll_code__courseUnit=courselet,
                    user=request.user,
                    state__isnull=False,
                    is_live=False,
                    is_preview=False,
                    is_test=False
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
                    liveSession.user.instructor.icon_url or static('img/student/avatar-teacher.jpg')
                )
            except AttributeError:
                liveSession.live_instructor_icon = static('img/student/avatar-teacher.jpg')
        courselets = self.get_courselets(request, course)
        live_sessions_history = Chat.objects.filter(
            user=request.user,
            is_live=True,
            enroll_code__courseUnit__course=course,
            # state__isnull=True
        )
        #     .annotate(
        #     lessons_done=models.Sum(
        #         models.Case(
        #             models.When(
        #                 message__contenttype='unitlesson',
        #                 message__kind='orct',
        #                 message__type='message',
        #                 message__owner=request.user,
        #                 then=1
        #             ),
        #             default=0,
        #             output_field=models.IntegerField()
        #         )
        #     )
        # )
        # live_sessions_history.filter(lessons_done=0).delete()

        # TODO: once django updated to version >=1.8 change next lines to
        # TODO: .annotate(lessons_count=models.Case()).
        # TODO: http://stackoverflow.com/questions/30752268/how-to-filter-objects-for-count-annotation-in-django
        #
        for chat in live_sessions_history:
            chat.lessons_done = Message.objects.filter(
                chat=chat,
                # contenttype='unitlesson',
                # kind='orct',
                # type='message',
                # owner=request.user,
                contenttype='response',
                kind='response',
                type='message',
                owner=request.user,
                timestamp__isnull=False,
            ).count()
            if not chat.lessons_done:
                chat.delete()

        return render(
            request,
            self.template_name,
            dict(
                course=course,
                liveSession=liveSession,
                courslets=courselets,
                livesessions=live_sessions_history,
            )
        )


class LMSTesterCourseView(NewLoginRequiredMixin, CourseView):

    template_name = 'lms/tester_course_page.html'

    def get_courselets(self, request, course):
        # User can see courselets only by getting here from the Shared Courses page
        # TODO: Cover this
        invites = Invite.objects.filter(user=self.request.user, course=course, status='joined', type='tester').distinct('enroll_unit_code__courseUnit') # pragma: no cover
        courselets = []
        if invites:
            for invite in invites:
                # backward compability for old Invites
                if not invite.enroll_unit_code:
                    first_courselet = course.courseunit_set.all().first()
                    if not first_courselet:
                        continue
                    invite.enroll_unit_code = EnrollUnitCode.get_code(first_courselet, give_instance=True)
                    invite.save()

                courselet = (
                    invite.enroll_unit_code.courseUnit,
                    EnrollUnitCode.get_code(invite.enroll_unit_code.courseUnit, isTest=True),
                    len(invite.enroll_unit_code.courseUnit.unit.get_exercises()),
                    Chat.objects.filter(
                        enroll_code__courseUnit=invite.enroll_unit_code.courseUnit,
                        user=request.user,
                        state__isnull=False,
                        is_live=False,
                        is_test=True,
                        is_preview=False
                    ).first()
                )
                courselets.append(courselet)
            return courselets
        raise Http404('Message')
