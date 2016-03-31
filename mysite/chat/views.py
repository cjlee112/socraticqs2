import injections
from django.views.generic import View
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import Chat, EnrollUnitCode
from .services import ProgressHandler
from ct.models import Unit, Role, UnitLesson


@injections.has
class ChatInitialView(View):
    """
    Entry point for Chat UI.
    """
    next_handler = injections.depends(ProgressHandler)

    @method_decorator(login_required)
    def get(self, request, enroll_key):
        enroll_code = get_object_or_404(EnrollUnitCode, enrollCode=enroll_key)
        courseUnit = enroll_code.courseUnit
        unit = courseUnit.unit
        if not Role.objects.filter(
            user=request.user.id, course=courseUnit.course, role=Role.ENROLLED
        ):
            enrolling = Role.objects.get_or_create(user=request.user,
                                                   course=courseUnit.course,
                                                   role=Role.SELFSTUDY)[0]
            enrolling.role = Role.ENROLLED
            enrolling.save()

        chat = Chat.objects.filter(enroll_code=enroll_code).first()
        if not chat and enroll_key:
            chat = Chat(
                user=request.user,
                enroll_code=enroll_code
            )
            chat.save(request)
        if chat.message_set.count() == 0:
            next_point = self.next_handler.start_point(unit=unit, chat=chat, request=request)
        else:
            next_point = chat.next_point

        lessons = unit.get_exercises()

        concepts = []
        for ul in unit.unitlesson_set.filter(lesson__concept__isnull=False, kind=UnitLesson.COMPONENT):
            title = ul.lesson.concept.title
            url = ul.lesson.url if ul.lesson.url else reverse(
                'ct:study_concept', args=(courseUnit.course.id, unit.id, ul.id)
            )
            concepts.append((title, url))

        return render(
            request,
            'chat/main_view.html',
            {
                'chat_id': chat.id,
                'course': courseUnit.course,
                'unit': unit,
                'concepts': concepts,
                'chat_id': chat.id,
                'lessons': lessons,
                'lesson_cnt': len(lessons),
                'duration': len(lessons) * 3,
                'next_point': next_point,
                'fsmstate': chat.state
            }
        )
