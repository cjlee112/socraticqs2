import injections
from django.views.generic import View
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import Chat, EnrollUnitCode
from .services import ProgressHandler
from ct.models import Unit, Role


@injections.has
class ChatInitialView(View):
    """
    Entry point for Chat UI.
    """
    next_handler = injections.depends(ProgressHandler)

    @method_decorator(login_required)
    def get(self, request, enroll_key):
        if enroll_key:
            courseUnit = get_object_or_404(EnrollUnitCode, enrollCode=enroll_key).courseUnit
            unit = courseUnit.unit
            if not Role.objects.filter(
                user=request.user.id, course=courseUnit.course, role=Role.ENROLLED
            ):
                enrolling = Role.objects.get_or_create(user=request.user,
                                                       course=courseUnit.course,
                                                       role=Role.SELFSTUDY)[0]
                enrolling.role = Role.ENROLLED
                enrolling.save()

        else:
            unit = Unit.objects.all().first()  # TODO add real Unit query
        chat = Chat.objects.all().first()  # TODO add real Chat query
        if not chat and enroll_key:
            chat = Chat(
                user=request.user,
                enroll_code=EnrollUnitCode.objects.filter(enrollCode=enroll_key).first()
            )
            chat.save(request)
        if chat.message_set.count() == 0:
            next_point = self.next_handler.start_point(unit=unit, chat=chat)
        else:
            next_point = chat.next_point
        return render(
            request,
            'chat/main_view.html',
            {
                'chat_id': chat.id,
                'lessons': unit.get_exercises(),
                'next_point': next_point
            }
        )
