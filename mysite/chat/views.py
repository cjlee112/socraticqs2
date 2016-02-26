from django.views.generic import View
from django.shortcuts import render


class ChatInitialView(View):
    """
    Entry point for Chat UI.
    """
    def get(self, request, enroll_key):
        return render(request, 'chat/main_view.html', locals())
