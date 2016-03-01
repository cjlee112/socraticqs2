import injections
from django.views.generic import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Chat
from .services import ProgressHandler
from ct.models import Unit


@injections.has
class ChatInitialView(View):
    """
    Entry point for Chat UI.
    """
    next_handler = injections.depends(ProgressHandler)

    def get(self, request, enroll_key=None):
        unit = Unit.objects.all().first()  # TODO add real Unit query
        chat = Chat.objects.all().first()  # TODO add real Chat query
        if not chat:
            chat = Chat.objects.create(user=request.user)
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
